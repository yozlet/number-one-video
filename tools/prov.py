#!/usr/bin/env python3
"""Provenance for the (gitignored) images under shots/.

The pixels are disposable; the recipe is not. Record it AT GENERATION TIME:
the commit SHA cannot be recovered afterwards, and a filename carries only
whatever the caller happened to put in it — `shots/cmp/mine_7.3.png` says
"timeline 7.3s" and nothing about the camera, tile size or build.

One JSON line per image in shots/provenance.jsonl (the last line for a path
wins, so re-rendering updates rather than appends history).
tools/manifest.py renders that into shots/MANIFEST.md.

From Python:
    from prov import record
    record(out, tool="tools/diff.py", argv=sys.argv, params={"timeline": times})

From shell:
    tools/prov.py record shots/x.png --tool tools/shoot.sh --param "url=/?t=1.0"
"""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "shots/provenance.jsonl")


def _git(*args):
    try:
        p = subprocess.run(("git", "-C", ROOT, *args), capture_output=True,
                           text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def commit():
    """HEAD of tracked sources, or None before the first commit exists."""
    return _git("rev-parse", "HEAD") or None


def dirty():
    """Tracked source files that differ from HEAD, i.e. why this build may not
    be reproducible from the commit alone."""
    out = _git("status", "--porcelain", "--", "index.html", "tools")
    if not out:
        return []
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return lines[:20] + (["…"] if len(lines) > 20 else [])


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dims(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            return list(im.size)
    except Exception:
        return None


def scrub(args):
    """Argv may hold absolute paths; a public repo should not carry one
    machine's home directory. Rewrite anything under ROOT to relative."""
    return [a.replace(ROOT + os.sep, "") if isinstance(a, str) else a
            for a in args]


def record(path, tool=None, argv=None, params=None, note=None):
    """Append one provenance entry for `path` (absolute or repo-relative)."""
    path = os.path.abspath(path)
    if not os.path.exists(path):
        print(f"prov: {path} does not exist, nothing recorded", file=sys.stderr)
        return None
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    entry = {
        "image": rel,
        "sha256": sha256(path),
        "bytes": os.path.getsize(path),
        "dims": dims(path),
        "generated_utc": datetime.datetime.now(datetime.timezone.utc)
                                 .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": tool,
        "argv": scrub(argv) if argv else None,
        "params": {k: (scrub(v) if isinstance(v, list) else scrub([v])[0])
                   for k, v in (params or {}).items()},
        "commit": commit(),
        "dirty": dirty(),
        "note": note,
    }
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def load():
    """Ledger as {image: entry}, last write winning."""
    if not os.path.exists(LEDGER):
        return {}
    out = {}
    with open(LEDGER) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            out[e["image"]] = e
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("image")
    r.add_argument("--tool", required=True)
    r.add_argument("--param", action="append", default=[],
                   help="key=value, repeatable")
    r.add_argument("--argv", nargs=argparse.REMAINDER,
                   help="arguments that produced the image")
    r.add_argument("--note")
    a = ap.parse_args()

    params = {}
    for kv in a.param:
        k, _, v = kv.partition("=")
        params[k] = v
    # A leftover --param after --argv would be swallowed by REMAINDER; refuse it
    # rather than silently dropping data from the one record we cannot redetect.
    argv = []
    for tok in a.argv or []:
        if tok.startswith("--param"):
            ap.error("put --param before --argv")
        argv.append(tok)
    e = record(a.image, tool=a.tool, argv=argv, params=params, note=a.note)
    if e:
        print(f"recorded {e['image']} ({e['sha256'][:12]}) "
              f"commit={(e['commit'] or 'none')[:7]}"
              f"{' dirty' if e['dirty'] else ''}")


if __name__ == "__main__":
    sys.exit(main())
