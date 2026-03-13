#!/bin/bash
# bon-soleil Holdings — OpenClaw entrypoint
# 初回セットアップ自動化

set -e

CONFIG_FILE="/home/node/.openclaw/openclaw.json"

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


# 引数をそのまま実行
exec "$@"
