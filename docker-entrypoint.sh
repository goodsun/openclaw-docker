#!/bin/bash
# bon-soleil Holdings — OpenClaw entrypoint
# 初回セットアップ自動化

set -e

CONFIG_FILE="/home/node/config/openclaw.yml"

# 初回起動時の設定
if [ ! -f "$CONFIG_FILE" ]; then
  echo "🚀 初回セットアップ中..."
  
  # openclaw setupを非対話モードで実行
  # .envから環境変数を読み取って設定される
  openclaw setup --non-interactive || {
    echo "⚠️  openclaw setup failed, trying gateway.mode=local"
    openclaw config set gateway.mode local
  }
  
  echo "✅ セットアップ完了"
fi

# 引数をそのまま実行
exec "$@"
