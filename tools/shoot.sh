#!/usr/bin/env bash
# Headless screenshot of the dev server, via Playwright's chrome-headless-shell.
#
# Usage:  tools/shoot.sh <path-or-url> <out.png> [width] [height]
#   e.g.  tools/shoot.sh / shots/act1.png
#
# WHY chrome-headless-shell AND NOT "Google Chrome for Testing":
#   The full app bundle spawns a crowd of helper processes, makes a macOS Keychain
#   lookup for its password store (which pops an unlock prompt), and attempts GCM
#   registration. On a loaded machine all of that can wedge it so it never exits --
#   `--dump-dom about:blank` hangs indefinitely and writes nothing. The headless
#   shell is the purpose-built binary: no keychain, no profile prompts, no GCM,
#   and it exits cleanly. Use it.
#
#   If a run ever does hang, the cause is usually machine load rather than the
#   page: bump WAIT and retry before debugging anything else.

set -euo pipefail

TARGET="${1:-/}"
OUT="${2:-shots/out.png}"
WIDTH="${3:-1280}"
HEIGHT="${4:-720}"
PORT="${PORT:-8731}"
WAIT="${WAIT:-120}"          # max seconds to wait for the screenshot
BUDGET="${BUDGET:-15000}"    # virtual-time budget: let CDN + WebGL init settle

SHELL_BIN="$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-mac-arm64/chrome-headless-shell"
[ -x "$SHELL_BIN" ] || { echo "headless shell not found at: $SHELL_BIN" >&2; exit 1; }

case "$TARGET" in
  http*) URL="$TARGET" ;;
  *)     URL="http://localhost:${PORT}${TARGET}" ;;
esac

mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
SERVER_PID=""

cleanup() {
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Start a server only if we're targeting localhost and nothing is listening.
if [[ "$URL" == http://localhost:* ]] && ! curl -sf -o /dev/null "$URL"; then
  # `exec` so $! is the python process itself, not a wrapping subshell that would
  # leave an orphaned server behind when the trap fires.
  (cd "$(dirname "$0")/.." && exec python3 -m http.server "$PORT" >/dev/null 2>&1) &
  SERVER_PID=$!
  for _ in $(seq 1 60); do
    curl -sf -o /dev/null "$URL" && break
    sleep 0.25
  done
fi

LOG="$(mktemp)"
"$SHELL_BIN" \
  --no-sandbox \
  --hide-scrollbars \
  --enable-unsafe-swiftshader \
  --use-angle=swiftshader \
  --window-size="${WIDTH},${HEIGHT}" \
  --virtual-time-budget="$BUDGET" \
  --screenshot="$OUT" \
  "$URL" >"$LOG" 2>&1 &
PID=$!

# Poll for the file rather than assuming a fixed duration -- under load this
# takes far longer than it does on an idle machine.
for ((i = 0; i < WAIT; i++)); do
  sleep 1
  kill -0 "$PID" 2>/dev/null || break
done

if kill -0 "$PID" 2>/dev/null; then
  kill -9 "$PID" 2>/dev/null || true
  wait "$PID" 2>/dev/null || true
  echo "TIMEOUT after ${WAIT}s (machine likely loaded -- retry with WAIT=300)" >&2
  exit 1
fi
wait "$PID" 2>/dev/null || true

grep -iE "uncaught|syntaxerror|typeerror|referenceerror" "$LOG" || true
rm -f "$LOG"

if [ ! -s "$OUT" ]; then
  echo "FAILED: no screenshot produced" >&2
  exit 1
fi
# Record the recipe: these images are gitignored, and the commit sha cannot be
# recovered after the fact. See tools/prov.py / shots/MANIFEST.md.
python3 "$(dirname "$0")/prov.py" record "$OUT" --tool tools/shoot.sh \
  --param "url=$URL" --param "window=${WIDTH}x${HEIGHT}" \
  --param "budget=$BUDGET" --param "wait=${i}s" || true
echo "ok after ~${i}s"
ls -la "$OUT"
