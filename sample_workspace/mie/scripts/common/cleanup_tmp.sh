#!/bin/bash
# bon-soleil Holdings — assets/tmp クリーンアップ
#
# 7日以上経過したファイルを削除。cronまたはAIエージェントから定期実行。
#
# Usage: bash scripts/common/cleanup_tmp.sh
# Cron例: 0 3 * * 0 cd ~/branch_office && bash scripts/common/cleanup_tmp.sh

set -e

WORKSPACE="${WORKSPACE:-$HOME/workspace}"
TMP_DIR="$WORKSPACE/assets/tmp"

if [ ! -d "$TMP_DIR" ]; then
  echo "[cleanup] $TMP_DIR not found, skipping."
  exit 0
fi

# .gitkeep は除外
COUNT=$(find "$TMP_DIR" -type f ! -name '.gitkeep' -mtime +7 | wc -l | tr -d ' ')

if [ "$COUNT" -eq 0 ]; then
  echo "[cleanup] No files older than 7 days in assets/tmp/. Clean!"
  exit 0
fi

echo "[cleanup] Removing $COUNT file(s) older than 7 days from assets/tmp/..."
find "$TMP_DIR" -type f ! -name '.gitkeep' -mtime +7 -print -delete

# 空ディレクトリも掃除
find "$TMP_DIR" -type d -empty ! -path "$TMP_DIR" -delete 2>/dev/null || true

echo "[cleanup] Done."
