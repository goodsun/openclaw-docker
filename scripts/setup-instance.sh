#!/bin/bash
# bon-soleil Holdings — Instance setup script
# セキュアな初期セットアップを自動化
#
# Usage: ./scripts/setup-instance.sh <instance-name> [-f|--force]
# Example: ./scripts/setup-instance.sh alice
# Example: ./scripts/setup-instance.sh alice -f  # 上書き確認なし

set -e

FORCE=false

# オプション解析
while [[ $# -gt 0 ]]; do
  case $1 in
    -f|--force)
      FORCE=true
      shift
      ;;
    *)
      INSTANCE=$1
      shift
      ;;
  esac
done

if [ -z "$INSTANCE" ]; then
  echo "❌ エラー: インスタンス名を指定してください"
  echo "Usage: $0 <instance-name> [-f|--force]"
  echo "Example: $0 alice"
  echo "Example: $0 alice -f  # 上書き確認なし（CI/自動化用）"
  exit 1
fi

INSTANCE_DIR="./instances/$INSTANCE"

echo "🚀 インスタンスセットアップ: $INSTANCE"
echo "================================================"

# .env.example存在チェック
if [ ! -f ".env.example" ]; then
  echo "❌ エラー: .env.example が見つかりません"
  echo "リポジトリのルートディレクトリで実行してください"
  exit 1
fi

# ディレクトリ作成
echo "📁 ディレクトリ作成..."
mkdir -p "$INSTANCE_DIR"/{workspace,sessions,config}

# .env作成
if [ -f "$INSTANCE_DIR/.env" ]; then
  if [ "$FORCE" = true ]; then
    echo "⚠️  $INSTANCE_DIR/.env は既に存在します（--force: 上書きします）"
  else
    echo "⚠️  $INSTANCE_DIR/.env は既に存在します"
    read -p "上書きしますか？ [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "❌ セットアップをキャンセルしました"
      exit 0
    fi
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
