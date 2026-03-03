#!/bin/bash
# bon-soleil Holdings — Session cleanup script
# Mephi requirement: Phase 1承認条件
#
# Usage: ./scripts/cleanup-sessions.sh [days] [--dry-run]
# Default: 30日以前のセッションファイルを削除
# --dry-run: 削除せずにプレビューのみ

set -e

DAYS=${1:-30}
DRY_RUN=false

# オプション解析
if [[ "$2" == "--dry-run" ]] || [[ "$1" == "--dry-run" ]]; then
  DRY_RUN=true
  DAYS=${1:-30}
fi

INSTANCES_DIR="./instances"

if [ "$DRY_RUN" = true ]; then
  echo "🧹 セッション削除プレビュー（${DAYS}日以前）[DRY RUN]"
else
  echo "🧹 セッション削除スクリプト（${DAYS}日以前）"
fi
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
  
  if [ "$DRY_RUN" = true ]; then
    echo "   👁️  削除予定: ${OLD_FILES}ファイル"
    echo "   📄 ファイル一覧（最大10件）:"
    find "$SESSION_DIR" -name "*.jsonl" -type f -mtime +${DAYS} -print | head -10 | sed 's/^/      /'
    if [ "$OLD_FILES" -gt 10 ]; then
      echo "      ... 他 $((OLD_FILES - 10))ファイル"
    fi
  else
    echo "   🗑️  削除対象: ${OLD_FILES}ファイル"
    # 削除実行
    find "$SESSION_DIR" -name "*.jsonl" -type f -mtime +${DAYS} -delete
    echo "   ✅ 削除完了"
  fi
done

echo ""
echo "================================================"
if [ "$DRY_RUN" = true ]; then
  echo "✅ プレビュー完了（実際には削除されていません）"
  echo "💡 実行する場合: $0 $DAYS（--dry-runなし）"
else
  echo "✅ クリーンアップ完了"
fi
