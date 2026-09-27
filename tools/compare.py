#!/usr/bin/env python3
"""Side-by-side comparison: reference video frames vs our render.

Top row is the original video, bottom row is our Three.js scene, at matching
timestamps. Columns are chronological, labelled with the timecode.

This exists because eyeballing a render against a frame you looked at twenty
minutes ago does not work — the differences that matter (proportions, where a
part sits, how big a feature is) only become obvious when the two are adjacent.

Usage:
    tools/compare.py 1.0 2.8 6.6 9.0
    tools/compare.py --out shots/cmp/open.png --tile 480x270 4.2 7.4 8.6
"""
import argparse
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prov  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO = os.path.join(ROOT, "reference/video.mp4")
TMP = os.path.join(ROOT, "shots/cmp")

FONTS = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def font(size):
    for path in FONTS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def grab_video(t, w, h, out):
    """One frame from the source video at time t."""
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", VIDEO,
        "-frames:v", "1", "-vf", f"scale={w}:{h}", out,
    ]
    sh(cmd)
    prov.record(out, tool="tools/compare.py", argv=cmd,
                params={"source": "reference/video.mp4", "t": t,
                        "tile": f"{w}x{h}"},
                note=f"reference video @ t={t}s, {w}x{h}")
    return out


def grab_render(t, w, h, out):
    """One frame from our scene at timeline position t, HUD hidden."""
    script = os.path.join(ROOT, "tools/shoot.sh")
    url = f"/?t={t}&ui=0"
    sh([script, url, out, str(w), str(h)],
       env={**os.environ, "WAIT": "300"})
    prov.record(out, tool="tools/shoot.sh", argv=["tools/shoot.sh", url, out,
                                                  str(w), str(h)],
                params={"source": "index.html", "timeline": t, "ui": 0,
                        "tile": f"{w}x{h}"},
                note=f"our render, timeline t={t}s, HUD off, {w}x{h}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("times", nargs="+", type=float)
    ap.add_argument("--out", default=os.path.join(TMP, "compare.png"))
    ap.add_argument("--tile", default="640x360")
    ap.add_argument("--reuse", action="store_true",
                    help="reuse existing renders instead of re-shooting")
    args = ap.parse_args()

    w, h = (int(v) for v in args.tile.lower().split("x"))
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    cols = []
    for t in args.times:
        ref = os.path.join(TMP, f"ref_{t}.png")
        mine = os.path.join(TMP, f"mine_{t}.png")

        if not (args.reuse and os.path.exists(ref)):
            grab_video(t, w, h, ref)
        if not (args.reuse and os.path.exists(mine)):
            print(f"  rendering t={t} ...", flush=True)
            grab_render(t, w, h, mine)

        cols.append((t, Image.open(ref).convert("RGB"), Image.open(mine).convert("RGB")))

    # ── compose ──────────────────────────────────────────────────────────────
    pad, label_h, gutter = 6, 26, 84
    n = len(cols)
    W = gutter + n * w + (n + 1) * pad
    H = label_h + 2 * h + 3 * pad

    sheet = Image.new("RGB", (W, H), (26, 25, 23))
    d = ImageDraw.Draw(sheet)
    f_label, f_row = font(15), font(14)

    for i, (t, ref, mine) in enumerate(cols):
        x = gutter + pad + i * (w + pad)
        d.text((x + 2, 6), f"t = {t:g}s", font=f_label, fill=(232, 228, 218))
        sheet.paste(ref, (x, label_h))
        sheet.paste(mine, (x, label_h + pad + h))

    cx = gutter // 2
    d.text((cx, label_h + h // 2 - 8), "VIDEO", font=f_row, fill=(150, 145, 135),
           anchor="mm")
    d.text((cx, label_h + pad + h + h // 2 - 8), "RENDER", font=f_row,
           fill=(150, 145, 135), anchor="mm")

    sheet.save(args.out)
    prov.record(args.out, tool="tools/compare.py", argv=sys.argv,
                params={"times": args.times, "tile": args.tile},
                note="side-by-side sheet: video (top) vs render (bottom), same timestamps")
    print(f"{args.out}  ({sheet.width}x{sheet.height})")


if __name__ == "__main__":
    sys.exit(main())
