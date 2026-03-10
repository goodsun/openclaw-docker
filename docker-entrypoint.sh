#!/bin/bash
# bon-soleil Holdings — OpenClaw entrypoint
# 初回セットアップ自動化

set -e

CONFIG_FILE="/home/node/.openclaw/openclaw.json"
LABO_PORTAL_DIR="/home/node/labo_portal"
LABO_PORTAL_REPO="https://github.com/goodsun/labo_portal.git"

# 初回起動時の設定
if [ ! -f "$CONFIG_FILE" ] || [ "$(cat $CONFIG_FILE)" = "{}" ]; then
  echo "🚀 初回セットアップ中..."
  
  # Telegramなしの場合はlocalモード（TUI/WebChat）
  if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "📝 Telegramなし → localモード（TUI/WebChat）"
    openclaw config set gateway.mode local
    openclaw config set gateway.bind lan
  else
    echo "📱 Telegram設定あり → setup実行"
    openclaw setup --non-interactive || {
      echo "⚠️  openclaw setup failed, fallback to local mode"
      openclaw config set gateway.mode local
      openclaw config set gateway.apiKey "$ANTHROPIC_API_KEY"
    }
  fi
  
  echo "✅ セットアップ完了"
fi

# labo_portal のセットアップ（初回のみ clone）
if [ ! -d "$LABO_PORTAL_DIR/.git" ]; then
  echo "📦 labo_portal をクローン中..."
  git clone --depth=1 "$LABO_PORTAL_REPO" "$LABO_PORTAL_DIR"
  echo "✅ labo_portal クローン完了"
fi

# labo_portal ビルド（dist/が存在しない場合）
if [ ! -f "$LABO_PORTAL_DIR/dist/app.js" ]; then
  echo "🔨 labo_portal をビルド中..."
  cd "$LABO_PORTAL_DIR" && HOME=/tmp npm install --silent && HOME=/tmp npm run build
  cd /home/node
  echo "✅ labo_portal ビルド完了"
else
  echo "✅ labo_portal ビルド済み"
fi

# .env を labo_portal にコピー（マウントファイルから）
if [ -f "/home/node/.labo_portal_env" ]; then
  cp /home/node/.labo_portal_env "$LABO_PORTAL_DIR/.env"
  echo "✅ labo_portal .env セット完了"
fi

# 引数をそのまま実行
exec "$@"
