#!/usr/bin/env python3
"""Render shots/MANIFEST.md — every shot, how to rebuild it, and the commit it
came from.

The images under shots/ and reference/extracted/ are gitignored: they are
derived from the copyrighted source video and/or are large, and either way they
are regenerable. What is NOT regenerable is the recipe, so it lives here.

Two grades of entry, and the manifest says which is which:

  recorded   written by our tools at generation time (tools/prov.py): exact
             argv, timeline positions, tile sizes, and the commit plus whether
             the working tree was dirty. Reproducible.
  inferred   predates the ledger. The filename gives the source time; the rest
             is a guess based on how the tool is invoked today. Treat as a
             hint, not a guarantee.

Usage:  tools/manifest.py [--check]
        --check  non-zero exit if MANIFEST.md would change (pre-commit hook)
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prov  # noqa: E402

ROOT = prov.ROOT
SHOTS = os.path.join(ROOT, "shots")
SCAN = ["shots", "reference/extracted/frames"]
EXT = (".png", ".jpg", ".jpeg")

# ── inference for images that predate the ledger ─────────────────────────────
# Deliberately shallow: it reads what the filename actually encodes (a source
# time) and states today's invocation for that kind of shot. Anything richer
# would be invention, which is exactly what the recorded grade exists to avoid.

FF_REF = 'ffmpeg -ss {t} -i reference/video.mp4 -frames:v 1 -vf "scale={w}:{h}" {out}'


def infer(rel):
    """(what it shows, [rebuild commands]) for a ledger-less image."""
    d, name = os.path.split(rel)

    m = re.match(r"^ref_([\d.]+)\.png$", name)
    if d == "shots/cmp" and m:
        t = m.group(1)
        return (f"reference video @ t={t}s, 640x360 tile, in a comparison sheet",
                [f"tools/compare.py {t}  # also rewrites mine_{t}.png and compare.png",
                 FF_REF.format(t=t, w=640, h=360, out=rel)])
    if d == "shots/cmp" and (m := re.match(r"^mine_([\d.]+)\.png$", name)):
        t = m.group(1)
        return (f"our render, timeline t={t}s, HUD off, 640x360",
                [f"tools/compare.py {t}",
                 f'tools/shoot.sh "/?t={t}&ui=0" {rel} 640 360'])
    if d == "shots/cmp":
        return ("side-by-side sheet: video vs render, same timestamps",
                ["tools/compare.py <times...>"])
    if d == "shots/diff" and (m := re.match(r"^ref_([\d.]+)\.png$", name)):
        t = m.group(1)
        return (f"reference video @ t={t}s, 384x216 tile, for mask scoring",
                [f"tools/diff.py {t} --dump-masks",
                 FF_REF.format(t=t, w=384, h=216, out=rel)])
    if d == "shots/diff":
        return ("diff harness output: baked render band, extracted masks or "
                "worst-frame montage",
                ["tools/diff.py <times...> [--dump-masks]",
                 "tools/diff.py <times...> --selftest"])
    if d == "shots/key" and (m := re.match(r"^t([\d.]+)\.png$", name)):
        t = m.group(1)
        return (f"reference video @ t={t}s, full resolution",
                [FF_REF.format(t=t, w=1280, h=720, out=rel)])
    if d == "shots/rig" and (m := re.match(r"^robot_([\d.]+)\.png$", name)):
        t = m.group(1)
        return (f"our render, timeline t={t}s", [f'tools/shoot.sh "/?t={t}&ui=0" {rel}'])
    if d == "shots/rig":
        return ("rig/landmark inspection render", ["tools/shoot.sh <url> <out>"])
    if d == "shots/contacts" and (m := re.match(r"^(\w+?)_([\d.]+)-([\d.]+)s\.png$", name)):
        a, b = m.group(2), m.group(3)
        span = float(b) - float(a)
        return (f"reference video, {a}s–{b}s, 2 fps contact sheet",
                [f'ffmpeg -ss {a} -t {span:g} -i reference/video.mp4 '
                 f'-vf "fps=2,scale=320:-1,tile=4x6" -frames:v 1 {rel}'])
    if d == "shots/beats":
        return ("beat-by-beat montage", ["tools/compare.py <times...>"])
    if d == "reference/extracted/frames" and (m := re.match(r"^frame_(\d+)\.jpg$", name)):
        idx = int(m.group(1))
        return (f"reference video @ t={(idx - 1) * 2}s (sparse, 2s apart)",
                ["ffmpeg -i reference/video.mp4 -vf fps=1/2 -q:v 2 "
                 "reference/extracted/frames/frame_%04d.jpg"])
    return ("ad-hoc shot; arguments were not recorded",
            ["tools/shoot.sh <url> <out> [w] [h]"])


def collect():
    """[(rel, abs)] for every image on disk under SCAN, in stable order."""
    found = []
    for base in SCAN:
        for dirpath, _dirs, files in os.walk(os.path.join(ROOT, base)):
            for f in sorted(files):
                if f.lower().endswith(EXT):
                    p = os.path.join(dirpath, f)
                    found.append((os.path.relpath(p, ROOT).replace(os.sep, "/"), p))
    return sorted(found)


def esc(s):
    return s.replace("|", "\\|")


def rows(images, ledger):
    out = []
    for rel, abs_p in images:
        e = ledger.get(rel)
        if e:
            what = e.get("note") or ""
            if not what:  # derive a description from the recorded params
                pr = e.get("params") or {}
                bits = [f"{k}={v}" for k, v in sorted(pr.items()) if v != ""]
                what = ", ".join(bits) or "recorded by " + (e.get("tool") or "?")
            if e.get("argv"):
                rebuild = " ".join(e["argv"])
            elif e.get("tool"):
                rebuild = f"{e['tool']} <args not recorded>"
            origin = f"recorded @ {(e['commit'] or 'pre-commit')[:7]}"
            if e.get("dirty"):
                origin += " +dirty"
            sha = e.get("sha256", "")[:12]
        else:
            what, cmds = infer(rel)
            rebuild = cmds[0]
            origin = "inferred (pre-git)"
            sha = prov.sha256(abs_p)[:12]
        out.append((rel, what, rebuild, origin, sha))
    return out


def render():
    ledger = prov.load()
    images = collect()
    data = rows(images, ledger)

    by_dir = {}
    for r in data:
        by_dir.setdefault(os.path.dirname(r[0]), []).append(r)

    # 98 sparse frames of the same thing is noise, not information: one row.
    sparse = by_dir.pop("reference/extracted/frames", None)
    if sparse:
        rels = [r[0] for r in sparse]
        by_dir["reference/extracted/frames"] = [(
            f"{os.path.basename(rels[0])} … {os.path.basename(rels[-1])} "
            f"({len(rels)} files)",
            "reference video, t = (N−1) × 2s (sparse), full resolution",
            "ffmpeg -i reference/video.mp4 -vf fps=1/2 -q:v 2 "
            "reference/extracted/frames/frame_%04d.jpg",
            sparse[0][3],
            f"{sparse[0][4]} … {sparse[-1][4]}",
        )]

    L = []
    L.append("# Shot manifest\n")
    L.append("Every image under `shots/` and `reference/extracted/frames/` is "
             "gitignored — it is derived from the copyrighted source video, "
             "large, and regenerable. This file is the recipe, so a reader can "
             "rebuild any of them and verify they got the same image.\n")
    L.append("**To rebuild a shot:** check out the commit in the *origin* "
             "column, run the command in *rebuild*, then compare the file's "
             "sha256 against the last column.\n")
    L.append("- `recorded @ <sha>` — written by `tools/prov.py` at generation "
             "time. Exact arguments, timings and source commit. "
             "`+dirty` means `index.html` or `tools/` had uncommitted changes, "
             "so the sha alone is not enough (re-render to be sure).")
    L.append("- `inferred (pre-git)` — produced before this repo existed. The "
             "filename pins the source time; the rest of the command is how "
             "that tool is invoked *today*, not a record of what was run. "
             "Treat it as a hint.\n")
    L.append(f"Generated by `tools/manifest.py` from "
             f"`shots/provenance.jsonl` ({len(ledger)} entries, "
             f"{len(images)} images on disk). Regenerate with "
             "`tools/manifest.py`.\n")

    for d in sorted(by_dir):
        L.append(f"## {d}\n")
        L.append("| image | what it shows | rebuild | origin | sha256 |")
        L.append("|---|---|---|---|---|")
        for rel, what, rebuild, origin, sha in by_dir[d]:
            L.append(f"| `{os.path.basename(rel)}` | {esc(what)} | "
                     f"`{esc(rebuild)}` | {origin} | `{sha}` |")
        L.append("")

    missing = sorted(set(ledger) - {r[0] for r in data})
    if missing:
        L.append("## Ledger entries with no file on disk\n")
        L.append("Rendered once, since deleted — the recipe still stands.\n")
        for rel in missing:
            e = ledger[rel]
            L.append(f"- `{rel}` — {e.get('tool') or '?'} "
                     f"@ {(e.get('commit') or 'pre-commit')[:7]}")
        L.append("")

    return "\n".join(L).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    text = render()
    path = os.path.join(SHOTS, "MANIFEST.md")
    old = open(path).read() if os.path.exists(path) else None
    if args.check:
        if old != text:
            print("MANIFEST.md is out of date — run tools/manifest.py", file=sys.stderr)
            return 1
        print("MANIFEST.md up to date")
        return 0
    with open(path, "w") as f:
        f.write(text)
    print(f"{os.path.relpath(path, ROOT)}  ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
