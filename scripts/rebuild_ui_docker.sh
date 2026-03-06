#!/usr/bin/env bash
# Design/UI ပြင်ပြီးရင် Docker မှာ ပြောင်းမြင်ရအောင် frontend + backend image ပြန် build ပြီး restart
# Repo root မှ run ပါ: ./scripts/rebuild_ui_docker.sh
set -e
cd "$(dirname "$0")/.."
COMPOSE_FILE=compose/docker-compose.yml
COMPOSE="docker compose"
docker compose version >/dev/null 2>&1 || COMPOSE="docker-compose"

echo "🐳 Rebuilding frontend + backend (UI/design ပြင်ထားတာ ဒီ build မှာ ပါသွားမယ်)..."
$COMPOSE -f "$COMPOSE_FILE" up -d --build frontend backend
echo ""
echo "✅ ပြီးပါပြီ။ Browser မှာ Hard Refresh (Ctrl+Shift+R) သို့မဟုတ် cache ဖျက်ပြီး ပြန်ဖွင့်ပါ။"
echo "   App: http://localhost:${FRONTEND_PORT:-8888}/app/"
