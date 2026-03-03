#!/bin/bash
# bon-soleil Holdings — Session cleanup script
# Mephi requirement: Phase 1承認条件
#
# Usage: ./scripts/cleanup-sessions.sh [days]
# Default: 30日以前のセッションファイルを削除

set -e

DAYS=${1:-30}
INSTANCES_DIR="./instances"

echo "🧹 セッション削除スクリプト（${DAYS}日以前）"
echo "================================================"

for instance in alice mephi teddy; do
  SESSION_DIR="${INSTANCES_DIR}/${instance}/sessions"
  
  if [ ! -d "$SESSION_DIR" ]; then
    echo "⏭️  ${instance}: ディレクトリなし（スキップ）"
    continue
  fi
  
  echo ""
  echo "📂 ${instance}:"
  
  # 削除対象ファイル数確認
  OLD_FILES=$(find "$SESSION_DIR" -name "*.jsonl" -type f -mtime +${DAYS} 2>/dev/null | wc -l)
  
  if [ "$OLD_FILES" -eq 0 ]; then
    echo "   ✅ 削除対象なし"
    continue
  fi
  
  echo "   🗑️  削除対象: ${OLD_FILES}ファイル"
  
  # 削除実行
  find "$SESSION_DIR" -name "*.jsonl" -type f -mtime +${DAYS} -delete
  
  echo "   ✅ 削除完了"
done

echo ""
echo "================================================"
echo "✅ クリーンアップ完了"
