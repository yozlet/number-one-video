#!/usr/bin/env python3
"""Convert pi session JSONL into readable Markdown, permanently, in the project.

Sessions live in ~/.pi/agent/sessions/--<path>--/*.jsonl and embed every image as
base64 (this project's first session is 24.8MB, almost all of it frames). The raw
file is the archival original; this produces the transcript you can actually grep,
diff and read.

Idempotent: already-converted sessions are skipped, so it is safe to run repeatedly
(and cheap to run as part of the work — see AGENTS.md).

Usage:
  tools/session-log.py                 # convert anything new for this project
  tools/session-log.py --force         # re-convert everything
  tools/session-log.py --full          # don't truncate tool output
  tools/session-log.py --list          # show sessions and conversion state
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "log/sessions")

RESULT_CAP = 2500      # chars of tool output kept by default
THINK_CAP = 6000


def slug_for(path):
    """pi's session directory name for a cwd: leading / dropped, separators -> -"""
    return "--" + path.lstrip("/").replace("/", "-").replace("\\", "-").replace(":", "-") + "--"


def sessions_dir():
    return os.path.join(os.path.expanduser("~/.pi/agent/sessions"), slug_for(ROOT))


def clip(text, cap, label):
    if cap and len(text) > cap:
        return text[:cap] + f"\n\n_[{label} truncated — {len(text) - cap} more chars]_"
    return text


def fmt_ts(ms):
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    except Exception:
        return "?"


def args_brief(args):
    """Tool args, but never the giant ones. Images/paths are what matter for grep."""
    if not isinstance(args, dict):
        return str(args)[:200]
    out = {}
    for k, v in args.items():
        s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
        out[k] = s if len(s) <= 300 else s[:300] + "…"
    return json.dumps(out, ensure_ascii=False)


def convert(src, full=False):
    lines = open(src, encoding="utf-8", errors="replace").read().splitlines()
    out = []
    calls = {}          # toolCallId -> (name, args)
    header = None
    stats = {"user": 0, "assistant": 0, "tools": 0, "images": 0}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = o.get("type")

        if t == "session":
            header = o
            continue
        if t == "compaction":
            out.append("\n---\n\n## ⚑ context compacted here\n")
            continue
        if t == "model_change":
            out.append(f"\n_[model → {o.get('model') or o.get('modelId') or '?'}]_\n")
            continue
        if t != "message":
            continue

        m = o.get("message", {})
        role = m.get("role")
        content = m.get("content")

        if role == "system":
            continue          # harness preamble, not conversation
        if role == "user":
            stats["user"] += 1
            txt = content if isinstance(content, str) else "".join(
                b.get("text", "") for b in content if isinstance(b, dict))
            out.append(f"\n---\n\n## USER\n\n{txt.strip()}\n")

        elif role == "assistant":
            stats["assistant"] += 1
            out.append(f"\n---\n\n## ASSISTANT  \n`{fmt_ts(m.get('timestamp'))}`\n")
            for b in (content or []):
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                if bt == "thinking" and b.get("thinking"):
                    out.append("\n### thinking\n\n"
                               + clip(b["thinking"].strip(), None if full else THINK_CAP, "thinking") + "\n")
                elif bt == "text" and b.get("text"):
                    out.append("\n" + b["text"].strip() + "\n")
                elif bt == "toolCall":
                    name, args = b.get("name"), b.get("arguments")
                    calls[b.get("id")] = (name, args)
                    stats["tools"] += 1
                    out.append(f"\n#### → `{name}`\n\n```json\n{args_brief(args)}\n```\n")

        elif role == "toolResult":
            name, args = calls.get(m.get("toolCallId"), (m.get("toolName"), None))
            label = name or m.get("toolName") or "?"
            parts = []
            for b in (m.get("content") or []):
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                if bt == "text":
                    parts.append(b.get("text", ""))
                elif bt == "image":
                    stats["images"] += 1
                    # point at what was read rather than embedding base64
                    src_hint = ""
                    if isinstance(args, dict):
                        src_hint = args.get("path") or args.get("url") or ""
                    parts.append(f"_[image{f' → {src_hint}' if src_hint else ''}]_")
                else:
                    parts.append(f"_[{bt}]_")
            body = "\n".join(parts).strip()
            err = "  **(error)**" if m.get("isError") else ""
            out.append(f"\n#### ← result `{label}`{err}\n\n"
                       + clip(body, None if full else RESULT_CAP, "result") + "\n")

    # header block
    head = [f"# Session transcript\n"]
    head.append(f"- source: `{os.path.relpath(src, ROOT)}`")
    head.append(f"- messages: {stats['user']} user · {stats['assistant']} assistant · "
                f"{stats['tools']} tool calls · {stats['images']} images")
    if header:
        for k in ("cwd", "version", "id"):
            if header.get(k) is not None:
                head.append(f"- {k}: `{header[k]}`")
    head.append(f"- converted: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%MZ')}")
    head.append("\n> Tool output is truncated by default; images are replaced by their "
                "source path. Re-run with `--full` for untruncated output.\n")
    return "\n".join(head) + "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    d = sessions_dir()
    if not os.path.isdir(d):
        print(f"no sessions for this project at:\n  {d}", file=sys.stderr)
        return 1

    files = sorted(f for f in os.listdir(d) if f.endswith(".jsonl"))
    if not files:
        print("no session files", file=sys.stderr)
        return 1

    os.makedirs(OUTDIR, exist_ok=True)
    converted = skipped = 0
    for f in files:
        src = os.path.join(d, f)
        stem = re.sub(r"\.jsonl$", "", f)
        dest = os.path.join(OUTDIR, stem + ".md")
        exists = os.path.exists(dest)
        if args.list:
            print(f"{'converted' if exists else 'PENDING  '}  {f}")
            continue
        if exists and not args.force:
            skipped += 1
            continue
        md = convert(src, args.full)
        open(dest, "w", encoding="utf-8").write(md)
        size = os.path.getsize(dest) / 1024
        print(f"wrote {os.path.relpath(dest, ROOT)}  ({size:.0f} KB, "
              f"from {os.path.getsize(src)/1048576:.1f} MB)")
        converted += 1

    if not args.list:
        print(f"{converted} converted, {skipped} already current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
