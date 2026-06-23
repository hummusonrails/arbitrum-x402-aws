#!/usr/bin/env bash
#
# One command to run the whole live demo: start the web companion in the
# background, open it in the browser, then run the CLI driver in the foreground.
# The web server is shut down automatically when the driver exits.
#
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

WEB_LOG="/tmp/x402-demo-web.log"
URL="http://localhost:3000"

# Start fresh: the companion should show the idle screen until the driver syncs.
rm -f "$REPO_ROOT/.demo-sync.json"

cleanup() {
  # Free port 3000 (kills the Next dev server and its children).
  lsof -ti tcp:3000 2>/dev/null | xargs kill 2>/dev/null || true
  kill "${WEB_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting the web companion (logs: $WEB_LOG) ..."
( cd "$REPO_ROOT/apps/web" && pnpm dev ) >"$WEB_LOG" 2>&1 &
WEB_PID=$!

# Wait for the companion to answer (up to ~30s).
ready=0
for _ in $(seq 1 60); do
  if curl -s -o /dev/null "$URL/api/sync" 2>/dev/null; then ready=1; break; fi
  sleep 0.5
done

if [ "$ready" = "1" ]; then
  echo "Companion is up at $URL — opening it in your browser."
  open "$URL" >/dev/null 2>&1 || true
else
  echo "WARNING: companion did not start (see $WEB_LOG). The CLI demo will still run."
fi

echo
# Run the driver in the foreground so it owns the terminal (Enter to advance).
cd "$REPO_ROOT/apps/agent" && uv run python ../../scripts/demo.py demo
