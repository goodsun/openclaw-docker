#!/bin/bash
# labo_portal を指定コンテナ内でpull & rebuild するスクリプト
# 使い方: sh scripts/update_labo_portal.sh [service名]
# 例: sh scripts/update_labo_portal.sh mephi
#     sh scripts/update_labo_portal.sh abu
#     sh scripts/update_labo_portal.sh  # 全コンテナ

DOCKER="${DOCKER:-$(command -v docker || echo ~/.rd/bin/docker)}"
SERVICES=${1:-mephi abu}

for SERVICE in $SERVICES; do
  CONTAINER="${SERVICE}-openclaw"
  echo "🔄 [$CONTAINER] labo_portal を更新中..."

  $DOCKER exec "$CONTAINER" sh -c "
    cd /home/node/labo_portal && \
    git pull && \
    HOME=/tmp npm install --silent && \
    HOME=/tmp npm run build && \
    echo '✅ ビルド完了'
  "

  if [ $? -eq 0 ]; then
    echo "🔁 [$CONTAINER] 再起動中..."
    $DOCKER restart "$CONTAINER"
    echo "✅ [$CONTAINER] 更新完了"
  else
    echo "❌ [$CONTAINER] 更新失敗"
  fi
done
