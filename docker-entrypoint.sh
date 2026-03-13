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

# .env → openclaw.json 反映（起動毎に上書き。.envが唯一の設定源）
if [ -n "$OPENCLAW_MODEL" ]; then
  openclaw config set agents.defaults.model "$OPENCLAW_MODEL"
fi
if [ -n "$OPENCLAW_THINKING" ]; then
  openclaw config set agents.defaults.thinkingDefault "$OPENCLAW_THINKING"
fi
if [ -n "$OPENCLAW_BIND" ]; then
  openclaw config set gateway.bind "$OPENCLAW_BIND"
fi
if [ -n "$OPENCLAW_API_KEY" ]; then
  openclaw config set gateway.apiKey "$OPENCLAW_API_KEY"
fi

# .env を labo_portal にコピー（マウントファイルから）
if [ -f "/home/node/.labo_portal_env" ]; then
  cp /home/node/.labo_portal_env "$LABO_PORTAL_DIR/.env" 2>/dev/null || \
    echo "⚠️  labo_portal .env コピーできませんでした（読み取り専用の可能性）"
  echo "✅ labo_portal .env セット完了"
fi

# 引数をそのまま実行
exec "$@"
