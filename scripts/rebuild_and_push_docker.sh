#!/usr/bin/env bash
# Ubuntu 25.10 (နဲ့ အခြား host) မှာ Docker image တွေ အသစ်ပြန် build ပြီး လိုရင် registry ကို push လုပ်မယ်။
# Repo root မှ run ပါ: ./scripts/rebuild_and_push_docker.sh
# Push လုပ်ချင်ရင်: REGISTRY=your-registry.com/imagename ./scripts/rebuild_and_push_docker.sh
# သို့မဟုတ်: ./scripts/rebuild_and_push_docker.sh --push
set -e
cd "$(dirname "$0")/.."
COMPOSE_FILE=compose/docker-compose.yml
[ -f "$COMPOSE_FILE" ] || { echo "❌ Compose file not found: $COMPOSE_FILE (run from repo root)"; exit 1; }
COMPOSE="docker compose"
docker compose version >/dev/null 2>&1 || COMPOSE="docker-compose"

# Optional: no-cache build (သန့်သန့်နဲ့ ပြန် build ချင်ရင်)
NO_CACHE=""
PUSH=""
for arg in "$@"; do
  case "$arg" in
    --no-cache) NO_CACHE="--no-cache" ;;
    --push)     PUSH=1 ;;
  esac
done

echo "🐳 Rebuilding all images (Ubuntu 25.10–friendly; frontend + backend)..."
$COMPOSE -f "$COMPOSE_FILE" build $NO_CACHE frontend backend

echo ""
echo "🔄 Restarting stack..."
$COMPOSE -f "$COMPOSE_FILE" up -d frontend backend

if [ -n "$PUSH" ] || [ -n "$REGISTRY" ]; then
  REGISTRY="${REGISTRY:-}"
  if [ -z "$REGISTRY" ]; then
    echo "⚠️  --push သုံးထားပါတယ်။ REGISTRY=host/path သတ်မှတ်ပါ။ ဥပမာ: REGISTRY=ghcr.io/user/hobo-pos ./scripts/rebuild_and_push_docker.sh --push"
    exit 1
  fi
  echo "📤 Pushing images to $REGISTRY ..."
  for name in frontend backend; do
    id=$($COMPOSE -f "$COMPOSE_FILE" images -q $name 2>/dev/null | head -1)
    if [ -z "$id" ]; then
      echo "⚠️  Image for $name not found (run build first)."
      continue
    fi
    dest="$REGISTRY-$name:latest"
    docker tag "$id" "$dest" && docker push "$dest" || echo "⚠️  Push $dest failed (docker login?)."
  done
  echo "✅ Push ပြီးပါပြီ။"
else
  echo "✅ Rebuild ပြီးပါပြီ။ Browser မှာ Hard Refresh (Ctrl+Shift+R) လုပ်ပါ။"
  echo "   App: http://localhost:${FRONTEND_PORT:-8888}/app/"
  echo "   Push လုပ်ချင်ရင်: REGISTRY=your-registry ./scripts/rebuild_and_push_docker.sh --push"
fi
