#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════╗
# ║         Group-6 FinalCognate — Full System Launcher                 ║
# ║                                                                      ║
# ║  Services started:                                                   ║
# ║    • Classifier backend  → http://localhost:8000  (/predict)         ║
# ║    • EcoBot backend      → http://localhost:8001  (/chat)            ║
# ║    • Trash-UI frontend   → http://localhost:3000                     ║
# ╚══════════════════════════════════════════════════════════════════════╝

set -e

# ── Resolve the project root (wherever this script lives) ──────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         Group-6 FinalCognate — Full System Launcher                 ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Project root: $SCRIPT_DIR"
echo ""

# ── Dependency checks ──────────────────────────────────────────────────
command -v python >/dev/null 2>&1 || { echo "❌  Python not found. Install Python 3.10+."; exit 1; }
command -v node   >/dev/null 2>&1 || { echo "❌  Node.js not found. Install Node 18+."; exit 1; }
command -v npm    >/dev/null 2>&1 || { echo "❌  npm not found."; exit 1; }

# ── Load .env into this shell so backends inherit the API key ──────────
if [ -f ".env" ]; then
  echo "🔑  Loading .env …"
  set -o allexport
  source .env
  set +o allexport
  echo "    DEEPSEEK_MODEL = ${DEEPSEEK_MODEL:-<not set>}"
else
  echo "⚠️   No .env file found — chatbot will use default Ollama settings."
fi
echo ""

# ── Frontend: install node_modules if needed ───────────────────────────
if [ ! -d "frontend/trash-ui/node_modules" ]; then
  echo "📦  Installing frontend dependencies (first run) …"
  (cd frontend/trash-ui && npm install)
  echo ""
fi

# ── Helper: clean up child processes on Ctrl-C ─────────────────────────
PIDS=()
cleanup() {
  echo ""
  echo "🛑  Stopping all services …"
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait
  echo "✅  All services stopped."
}
trap cleanup SIGINT SIGTERM

# ══════════════════════════════════════════════════════════════════════
# 1. Classifier backend — port 8000
# ══════════════════════════════════════════════════════════════════════
echo "🚀  [1/3] Starting Classifier backend  →  http://localhost:8000"
(
  cd backend/trash-uibackend
  python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
) &
PIDS+=($!)
echo "    PID ${PIDS[-1]}"
echo ""

# Give the classifier a moment before starting the next service
sleep 1

# ══════════════════════════════════════════════════════════════════════
# 2. EcoBot chatbot backend — port 8001
# ══════════════════════════════════════════════════════════════════════
echo "🤖  [2/3] Starting EcoBot chatbot backend  →  http://localhost:8001"
(
  cd backend/llmchabotbackend
  python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
) &
PIDS+=($!)
echo "    PID ${PIDS[-1]}"
echo ""

sleep 1

# ══════════════════════════════════════════════════════════════════════
# 3. Next.js frontend — port 3000
# ══════════════════════════════════════════════════════════════════════
echo "🌐  [3/3] Starting Trash-UI frontend  →  http://localhost:3000"
(
  cd frontend/trash-ui
  npm run dev
) &
PIDS+=($!)
echo "    PID ${PIDS[-1]}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  All services launched.  Press Ctrl-C to stop everything."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Dashboard  →  http://localhost:3000"
echo "  Scan       →  http://localhost:3000/scan"
echo "  Chat       →  http://localhost:3000/chat"
echo "  Classifier API  →  http://localhost:8000/docs"
echo "  EcoBot API      →  http://localhost:8001/docs"
echo ""

# Wait for all background processes
wait
