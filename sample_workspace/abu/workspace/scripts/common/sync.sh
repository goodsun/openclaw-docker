#!/bin/bash
# bon-soleil Holdings — Branch Office Sync
#
# 本社(branch_officeリポジトリ)から共通ファイルを同期します。
# 共通ファイルは強制上書き（本社が正）。ローカル固有ファイルには触れません。
#
# Usage: cd ~/branch_office && git pull && bash scripts/common/sync.sh

set -e
trap 'echo "ERROR at line $LINENO"; exit 1' ERR

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
HOME_DIR="$HOME"
WORKSPACE="$HOME/workspace"

echo ""
echo "bon-soleil Holdings — Sync"
echo "================================"
echo "Source: $REPO_DIR"
echo ""

# Helper: copy contents if source has files (safe against empty dirs)
sync_dir() {
  local src="$1" dst="$2"
  if [ -d "$src" ] && ls "$src/"* &>/dev/null 2>&1; then
    mkdir -p "$dst"
    cp -r "$src/"* "$dst/"
    echo "[sync] $dst/"
  else
    echo "[skip] $dst/ (source empty)"
  fi
}

# ----- 1. 社則 (company_rules) — 強制上書き -----
sync_dir "$REPO_DIR/documents/company_rules" "$WORKSPACE/documents/company_rules"

# ----- 2. 共通スクリプト (scripts/common) — 強制上書き -----
sync_dir "$REPO_DIR/scripts/common" "$WORKSPACE/scripts/common"

# ----- 3. HR (profiles, charsheets) — workspace内に強制上書き -----
sync_dir "$REPO_DIR/HR" "$WORKSPACE/HR"

# ----- 4. assets/charsheets — workspace内に強制上書き -----
sync_dir "$REPO_DIR/assets/charsheets" "$WORKSPACE/assets/charsheets"

echo ""
echo "================================"
echo "Sync complete!"
echo ""
