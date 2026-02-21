#!/bin/bash
# Run the Privacy Agent platform
# Usage:
#   ./run_agent.sh server     — Start the web server (default)
#   ./run_agent.sh telegram   — Start the Telegram bot
#   ./run_agent.sh dev        — Start web server + Vite dev server (hot reload)
#   ./run_agent.sh build      — Build the React frontend

set -e
cd "$(dirname "$0")"

case "${1:-server}" in
  server)
    echo "Starting Privacy Agent server on http://localhost:8000"
    echo "Make sure GEMINI_API_KEY is set: export GEMINI_API_KEY='your-key'"
    uvicorn agent.server:app --host 0.0.0.0 --port 8000 --reload
    ;;
  telegram)
    echo "Starting Telegram bot..."
    echo "Make sure TELEGRAM_BOT_TOKEN is set: export TELEGRAM_BOT_TOKEN='your-token'"
    echo "Make sure GEMINI_API_KEY is set: export GEMINI_API_KEY='your-key'"
    python -m agent.telegram_bot
    ;;
  dev)
    echo "Starting dev mode (backend + frontend hot reload)..."
    uvicorn agent.server:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    cd web && npm run dev &
    FRONTEND_PID=$!
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
    wait
    ;;
  build)
    echo "Building React frontend..."
    cd web && npm run build
    echo "Built to agent/static/"
    ;;
  *)
    echo "Usage: ./run_agent.sh [server|telegram|dev|build]"
    exit 1
    ;;
esac
