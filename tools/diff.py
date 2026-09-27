#!/usr/bin/env python3
"""Numeric fidelity check: reference frame vs our render, per frame.

Compares SILHOUETTES, not pixels. Each frame is reduced to a handful of numbers,
so a whole sweep can be checked without reading a single image:

  iou    raw mask overlap, in frame space (position + scale + shape together)
  shape  overlap after normalising position and scale -> isolated shape error
  size   object size ratio, ref/render (<1 means we are too big)
  dx dy  bbox centre offset, as % of frame

A bad `shape` with good `size`/`dx`/`dy` means the geometry is wrong. A good
`shape` with bad `dx` means only the camera placement is wrong. Read the montage
of the worst frames only when the numbers say something is actually broken.

Usage:
  tools/diff.py 1.0 2.8 6.9 7.3 8.5 9.2
  tools/diff.py 7.3 7.9 --reuse          # re-measure without re-baking
  tools/diff.py 1.0 2.8 --thresh 14      # tune mask extraction
"""
import argparse
import math
import os
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prov  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO = os.path.join(ROOT, "reference/video.mp4")
OUT = os.path.join(ROOT, "shots/diff")

FONTS = ["/System/Library/Fonts/Menlo.ttc",
         "/System/Library/Fonts/Supplemental/Courier New.ttf",
         "/System/Library/Fonts/Supplemental/Arial.ttf"]


def font(size):
    for p in FONTS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


ANALYSIS = (320, 180)   # all masking happens at this resolution


def otsu(g):
    """Automatic luminance threshold, maximising between-class variance.
    256 bins, so a plain loop is fine and needs no numpy."""
    h = g.histogram()[:256]
    total = sum(h)
    sum_all = sum(i * h[i] for i in range(256))
    sum_b, w_b = 0.0, 0
    best, thr = -1.0, 128
    for i in range(256):
        w_b += h[i]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += i * h[i]
        m_b, m_f = sum_b / w_b, (sum_all - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > best:
            best, thr = var, i
    return thr


def mask_otsu(im):
    """Threshold by luminance. Correct for a SUBJECT ON A CONTRASTING FIELD —
    bright robot in a dark arena — which is most of Act 3.

    The SMALLER class is taken as the subject (small figure, large field).
    """
    g = im.convert("L").resize(ANALYSIS, Image.BOX)
    m = g.point(lambda v: 255 if v > otsu(g) else 0).convert("1")
    if count_on(m) > (ANALYSIS[0] * ANALYSIS[1]) / 2:
        m = ImageChops.invert(m)
    return m


def mask_edge(im):
    """Structure by high-pass, then closed and hole-filled.

    Correct where luminance thresholding fails: Act 1 is white-on-white, so Otsu
    splits noise and finds nothing, while the structure lives entirely in edges.

    Caveat: topological fill on an edge map has no reliable notion of which side is
    the subject, so this INVERTS on some frames. Only trust it when the coverage
    comes out plausible.
    """
    g = im.convert("L").resize(ANALYSIS, Image.BOX)
    hp = ImageChops.difference(g, g.filter(ImageFilter.GaussianBlur(9)))
    mad = hp.resize((1, 1), Image.BOX).getpixel((0, 0))
    m = hp.point(lambda v: 255 if v > max(2.0, 1.6 * mad) else 0).convert("1")
    m = (m.convert("L")
         .filter(ImageFilter.MaxFilter(5))
         .filter(ImageFilter.MinFilter(5)))
    inv = ImageChops.invert(m.convert("1")).convert("L")
    ImageDraw.floodfill(inv, (0, 0), 0)
    return ImageChops.lighter(m, inv).point(lambda v: 255 if v > 127 else 0).convert("1")


MODES = (("otsu", mask_otsu), ("edge", mask_edge))


def pick_masks(ref, mine):
    """Try every segmentation and keep the first that is PLAUSIBLE — i.e. it finds a
    real region in both frames (8-92% of frame) and the two agree on how much
    (within 12 points). Falls back to the closest agreement, flagged unreliable.

    No single segmentation works on every shot in this video: a bright robot on a
    dark floor is a luminance problem, and a white machine on a white void is a
    structure problem. Rather than guess per shot type, measure both.
    """
    best = None
    for mode, fn in MODES:
        a, b = fn(ref), fn(mine)
        area = ANALYSIS[0] * ANALYSIS[1]
        ca, cb = count_on(a) / area * 100, count_on(b) / area * 100
        ok = 8 <= min(ca, cb) and max(ca, cb) <= 92 and abs(ca - cb) <= 12
        gap = abs(ca - cb)
        if ok:
            return mode, a, b, ca, cb, True
        if best is None or gap < best[0]:
            best = (gap, mode, a, b, ca, cb)
    return best[1], best[2], best[3], best[4], best[5], False


def segment_reference(im, target_pct):
    """Segment the reference, choosing between candidate methods by which lands
    closest to the KNOWN coverage of our rendered silhouette.

    Our coverage is exact, so it is free information for disambiguating the
    reference — which is the only side that still needs inferring.
    """
    area = ANALYSIS[0] * ANALYSIS[1]
    best = None
    for mode, fn in MODES:
        m = fn(im)
        cov = count_on(m) / area * 100
        gap = abs(cov - target_pct)
        if best is None or gap < best[0]:
            best = (gap, mode, m, cov)
    gap, mode, m, cov = best
    return mode, m, cov, gap <= 10


def count_on(m):
    return m.histogram()[-1]


def iou(a, b):
    if a is None or b is None:
        return 0.0
    inter = count_on(ImageChops.logical_and(a, b))
    union = count_on(ImageChops.logical_or(a, b))
    return inter / union if union else 0.0


def normalised(m, size=160):
    """Crop to the bbox and rescale so the LONGER side is `size`, preserving
    aspect, then centre on a square. Removing position and scale but keeping
    aspect means this isolates shape while still punishing a wrong aspect."""
    box = m.getbbox()
    if not box:
        return None
    c = m.crop(box)
    w, h = c.size
    s = size / max(w, h)
    c = c.resize((max(1, round(w * s)), max(1, round(h * s))), Image.NEAREST)
    canvas = Image.new("1", (size, size), 0)
    canvas.paste(c, ((size - c.width) // 2, (size - c.height) // 2))
    return canvas


def bake(times, tile, reuse):
    """Render every requested time in ONE browser launch ("?bakeTs=")."""
    cw, ch = tile
    cols = min(len(times), 8)
    rows = math.ceil(len(times) / cols)
    sheet_path = os.path.join(OUT, "bake.png")
    if not (reuse and os.path.exists(sheet_path)):
        url = (f"/?bakeTs={','.join(str(t) for t in times)}"
               f"&cols={cols}&w={cw}&h={ch}")
        subprocess.run(
            # window must cover BOTH bands (beauty + silhouette) or Chrome clips it
            [os.path.join(ROOT, "tools/shoot.sh"), url, sheet_path,
             str(cols * cw), str(2 * rows * ch)],
            check=True, capture_output=True, text=True,
            env={**os.environ, "WAIT": "300"},
        )
        prov.record(sheet_path, tool="tools/shoot.sh",
                    argv=["tools/shoot.sh", url, "shots/diff/bake.png",
                          str(cols * cw), str(2 * rows * ch)],
                    params={"source": "index.html", "bake_ts": times,
                            "cols": cols, "tile": f"{cw}x{ch}",
                            "note": "two bands: beauty over silhouette"})
    sheet = Image.open(sheet_path).convert("RGB")
    beauty, sil = [], []
    for i in range(len(times)):
        x, y = (i % cols) * cw, (i // cols) * ch
        beauty.append(sheet.crop((x, y, x + cw, y + ch)))
        # second band holds the rendered silhouette pass
        y2 = y + rows * ch
        sil.append(sheet.crop((x, y2, x + cw, y2 + ch)))
    return beauty, sil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("times", nargs="+", type=float)
    ap.add_argument("--tile", default="384x216")
    ap.add_argument("--thresh", type=int, default=None,
                    help="force a luminance threshold; default is Otsu per image")
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--debug-thresh", action="store_true",
                    help="print the adaptive threshold chosen per image")
    ap.add_argument("--worst", type=int, default=4,
                    help="how many worst frames to put in the montage")
    ap.add_argument("--selftest", action="store_true",
                    help="compare each reference frame against ITSELF; every score "
                         "must be 1.00 or the instrument is broken and no "
                         "ref-vs-render number can be trusted")
    ap.add_argument("--dump-masks", action="store_true",
                    help="write extracted masks for inspection — verify the "
                         "instrument before trusting its readings")
    args = ap.parse_args()

    cw, ch = (int(v) for v in args.tile.lower().split("x"))
    os.makedirs(OUT, exist_ok=True)

    if args.selftest:
        print(f"{'frame':>8} {'mode':>5} {'covA':>6} {'covB':>6} {'iou':>6} {'shape':>6}")
        bad = 0
        for t in args.times:
            p = os.path.join(OUT, f"ref_{t}.png")
            im = Image.open(p).convert("RGB")
            mode, a, b, ca, cb, _ = pick_masks(im, im)
            v, sh = iou(a, b), iou(normalised(a), normalised(b))
            if v < 0.999 or sh < 0.999:
                bad += 1
            print(f"{t:>8g} {mode:>5} {ca:>6.1f} {cb:>6.1f} {v:>6.2f} {sh:>6.2f}")
        print("INSTRUMENT OK" if not bad else f"INSTRUMENT BROKEN on {bad} frame(s)")
        return 0 if not bad else 1

    print(f"baking {len(args.times)} frames ...", flush=True)
    mine, sil = bake(args.times, (cw, ch), args.reuse)

    rows = []
    for i, (t, m) in enumerate(zip(args.times, mine)):
        ref_p = os.path.join(OUT, f"ref_{t}.png")
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", VIDEO,
               "-frames:v", "1", "-vf", f"scale={cw}:{ch}", ref_p]
        subprocess.run(cmd, check=True, capture_output=True)
        prov.record(ref_p, tool="tools/diff.py", argv=cmd,
                    params={"source": "reference/video.mp4", "t": t,
                            "tile": f"{cw}x{ch}"},
                    note=f"reference video @ t={t}s, {cw}x{ch}, for mask scoring")
        ref = Image.open(ref_p).convert("RGB")

        # Our side needs no segmentation at all: use the rendered silhouette pass.
        # Only the reference has to be inferred, which halves the problem.
        # Our side needs no segmentation: use the rendered silhouette pass.
        # resize to the SAME grid as the reference mask — comparing masks of
        # different sizes silently inflated the count and broke the IoU
        mb = (sil[i].convert("L").resize(ANALYSIS, Image.BOX)
              .point(lambda v: 255 if v > 127 else 0).convert("1"))
        cov_b = count_on(mb) / (ANALYSIS[0] * ANALYSIS[1]) * 100
        # Only the REFERENCE has to be inferred now — which halves the problem, and
        # leaves us a way to disambiguate: our coverage is known exactly, so pick
        # whichever reference segmentation lands closest to it.
        mode, ma, cov_a, reliable = segment_reference(ref, cov_b)
        if args.dump_masks:
            for mask, label in ((ma, "reference"), (mb, "render")):
                p = os.path.join(OUT, f"mask_{'ref' if label == 'reference' else 'mine'}_{t}.png")
                mask.save(p)
                prov.record(p, tool="tools/diff.py", argv=sys.argv,
                            params={"t": t, "mask_of": label, "mode": mode,
                                    "note": f"extracted {label} mask, t={t}s"})
        ba, bb = ma.getbbox(), mb.getbbox()
        if not ba or not bb:
            print(f"  t={t:<6g} no object isolated")
            continue

        wa, ha = ba[2] - ba[0], ba[3] - ba[1]
        wb, hb = bb[2] - bb[0], bb[3] - bb[1]
        size = math.sqrt((wa / wb) * (ha / hb))
        aw, ah = ANALYSIS
        dx = ((ba[0] + ba[2]) - (bb[0] + bb[2])) / 2 / aw * 100
        dy = ((ba[1] + ba[3]) - (bb[1] + bb[3])) / 2 / ah * 100

        rows.append({
            "t": t, "iou": iou(ma, mb),
            "shape": iou(normalised(ma), normalised(mb)),
            "size": size, "dx": dx, "dy": dy,
            "mode": mode, "reliable": reliable,
            "cov_a": cov_a, "cov_b": cov_b,
            "imgs": (ref, m),
        })

    if not rows:
        print("nothing measured", file=sys.stderr)
        return 1

    print(f"\n{'t':>7} {'iou':>6} {'shape':>6} {'size':>6} {'dx%':>7} {'dy%':>7} "
          f"{'mask%':>11} {'mode':>5}  note")
    for r in rows:
        note = []
        # Segmentation finds DETAIL, not objects. On a flat macro frame with little
        # high-frequency content (ours) against grainy video, the two masks are not
        # comparable and every derived number is meaningless. Say so rather than
        # reporting a confident wrong answer.
        if not r["reliable"]:
            note.append("MASK UNRELIABLE")
        else:
            if r["size"] < 0.94: note.append("TOO BIG")
            elif r["size"] > 1.06: note.append("too small")
            if abs(r["dx"]) > 4: note.append("shift x")
            if abs(r["dy"]) > 4: note.append("shift y")
            if r["shape"] < 0.75: note.append("SHAPE")
        print(f"{r['t']:>7g} {r['iou']:>6.2f} {r['shape']:>6.2f} {r['size']:>6.2f} "
              f"{r['dx']:>7.1f} {r['dy']:>7.1f} "
              f"{r['cov_a']:>5.0f}/{r['cov_b']:<5.0f} {r['mode']:>5} {' '.join(note)}")
    good = [r for r in rows if r["reliable"]]
    if good:
        print(f"\nusable frames {len(good)}/{len(rows)}"
              f"   mean iou {sum(r['iou'] for r in good)/len(good):.2f}"
              f"   mean shape {sum(r['shape'] for r in good)/len(good):.2f}")
    else:
        print("\nno frames with reliable masks")

    # montage of the worst, so the one image read targets the real problems
    worst = sorted(rows, key=lambda r: r["shape"])[:args.worst]
    worst.sort(key=lambda r: r["t"])
    pad, lab = 6, 26
    n = len(worst)
    W = n * cw + (n + 1) * pad
    H = lab + 2 * ch + 3 * pad
    sheet = Image.new("RGB", (W, H), (26, 25, 23))
    d = ImageDraw.Draw(sheet)
    f = font(15)
    for i, r in enumerate(worst):
        x = pad + i * (cw + pad)
        d.text((x + 2, 5), f"t = {r['t']:g}s   shape {r['shape']:.2f}",
               font=f, fill=(232, 228, 218))
        sheet.paste(r["imgs"][0], (x, lab))
        sheet.paste(r["imgs"][1], (x, lab + pad + ch))
    out = os.path.join(OUT, "worst.png")
    sheet.save(out)
    prov.record(out, tool="tools/diff.py", argv=sys.argv,
                params={"times": args.times, "tile": args.tile,
                        "worst": [r["t"] for r in worst],
                        "note": "worst-N frames by shape error, video over render"})
    print(f"worst {n} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
