#!/usr/bin/env python3
"""Measure how much of the frame the machine occupies, for a reference frame and
our render at the same timestamp.

Calibrating camera distance by eye is slow and drifts. This gives a number: the
object's bounding box as a fraction of frame width/height, for both images, so the
distance can be scaled by the ratio.

Method: high-pass the image (original minus a heavily blurred copy) and threshold.
The machine has structure; the studio background is a smooth gradient or flat
colour, so it drops out. Using a high-pass rather than a plain threshold means a
gradient background does not register as "object".

Usage:  tools/framing.py 7.3 8.5 9.2
        tools/framing.py --tile 440x248 7.3
"""
import argparse
import os
import sys

from PIL import Image, ImageChops, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, "shots/cmp")


def coverage(path):
    im = Image.open(path).convert("L")
    w, h = im.size
    hp = ImageChops.difference(im, im.filter(ImageFilter.GaussianBlur(14)))
    bw = hp.point(lambda v: 255 if v > 9 else 0)
    bbox = bw.getbbox()
    if not bbox:
        return None
    x0, y0, x1, y1 = bbox
    return {
        "w": (x1 - x0) / w,
        "h": (y1 - y0) / h,
        "cx": ((x0 + x1) / 2) / w,
        "cy": ((y0 + y1) / 2) / h,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("times", nargs="+")
    ap.add_argument("--tile", default="440x248")
    args = ap.parse_args()

    print(f"{'t':>7} {'REF w x h':>15} {'RENDER w x h':>15} "
          f"{'zoom':>6} {'REF cy':>7} {'R cy':>7}")
    for t in args.times:
        ref = os.path.join(TMP, f"ref_{t}.png")
        mine = os.path.join(TMP, f"mine_{t}.png")
        if not (os.path.exists(ref) and os.path.exists(mine)):
            print(f"{t:>7}  (missing — run tools/compare.py first)")
            continue
        a, b = coverage(ref), coverage(mine)
        if not a or not b:
            print(f"{t:>7}  (could not isolate object)")
            continue
        # zoom < 1 => we are too small, so DIVIDE the camera distance by it
        zoom = ((a["w"] / b["w"]) + (a["h"] / b["h"])) / 2
        print(f"{t:>7}  {a['w']*100:5.1f}% x{a['h']*100:5.1f}% "
              f"{b['w']*100:5.1f}% x{b['h']*100:5.1f}% "
              f"{zoom:>6.2f} {a['cy']*100:6.1f}% {b['cy']*100:6.1f}%")


if __name__ == "__main__":
    sys.exit(main())
