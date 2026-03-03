#!/bin/bash
# bon-soleil Holdings — Instance setup script
# セキュアな初期セットアップを自動化
#
# Usage: ./scripts/setup-instance.sh <instance-name>
# Example: ./scripts/setup-instance.sh alice

set -e

if [ -z "$1" ]; then
  echo "❌ エラー: インスタンス名を指定してください"
  echo "Usage: $0 <instance-name>"
  echo "Example: $0 alice"
  exit 1
fi

INSTANCE=$1
INSTANCE_DIR="./instances/$INSTANCE"

echo "🚀 インスタンスセットアップ: $INSTANCE"
echo "================================================"

# ディレクトリ作成
echo "📁 ディレクトリ作成..."
mkdir -p "$INSTANCE_DIR"/{workspace,sessions,config}

# .env作成
if [ -f "$INSTANCE_DIR/.env" ]; then
  echo "⚠️  $INSTANCE_DIR/.env は既に存在します"
  read -p "上書きしますか？ [y/N]: " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ セットアップをキャンセルしました"
    exit 0
  fi
fi

echo "📝 .envファイル作成..."
cp .env.example "$INSTANCE_DIR/.env"

# パーミッション設定（セキュリティ重要）
echo "🔒 パーミッション設定（chmod 600）..."
chmod 600 "$INSTANCE_DIR/.env"

echo ""
echo "================================================"
echo "✅ セットアップ完了！"
echo ""
echo "次のステップ:"
echo "  1. エディタで .env を編集:"
echo "     vim $INSTANCE_DIR/.env"
echo ""
echo "  2. 必須項目を設定:"
echo "     - CONTAINER_UID/CONTAINER_GID（macOS: 501/20、Linux: 1000/1000）"
echo "     - ANTHROPIC_API_KEY"
echo "     - TELEGRAM_BOT_TOKEN"
echo ""
echo "  3. コンテナ起動:"
echo "     docker-compose up -d $INSTANCE"
echo ""
