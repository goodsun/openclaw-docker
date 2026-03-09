#!/bin/bash
# daily_report.sh — bon-soleil OpenClaw デイリーレポートサンプル
#
# 使い方:
#   1. このスクリプトをサーバー上に配置
#   2. crontab -e で定刻実行を設定（例: 毎朝9時）
#      0 9 * * * /path/to/daily_report.sh
#
# 動作:
#   - df / free / エラーログ等のシステム情報を収集
#   - OpenClawエージェントにレポート作成を依頼
#   - エージェントがTelegramへ送信
#
# 前提:
#   - OpenClaw gatewayが起動していること
#   - Telegramチャンネルが設定済みであること

set -e

# --- 設定 ---
OPENCLAW_CMD="openclaw"          # OpenClawコマンド（パス調整すること）
TODAY=$(date '+%Y-%m-%d %H:%M')

# --- システム情報を収集 ---
DISK_USAGE=$(df -h / | tail -1 | awk '{print "使用: "$3" / "$2" ("$5")"}')
MEMORY=$(free -h | awk '/^Mem:/ {print "使用: "$3" / "$2}')
LOAD=$(uptime | awk -F'load average:' '{print $2}' | xargs)
UPTIME=$(uptime -p)

# Dockerコンテナ状態（Dockerが使える場合）
if command -v docker &> /dev/null; then
  CONTAINERS=$(docker ps --format "{{.Names}}: {{.Status}}" 2>/dev/null | head -10 || echo "取得失敗")
else
  CONTAINERS="（Docker未使用）"
fi

# エラーログサマリ（直近1時間のERROR/WARN）
ERROR_COUNT=$(journalctl --since "1 hour ago" -p err 2>/dev/null | wc -l || echo "0")

# --- OpenClawにレポート作成を依頼 ---
MESSAGE=$(cat <<EOF
以下の情報をもとに、今日のシステム状況レポートを作成してTelegramで送信してください。
数値は見やすく整形し、最後にその日にふさわしい一言を添えてください。

【日時】${TODAY}
【ディスク】${DISK_USAGE}
【メモリ】${MEMORY}
【ロードアベレージ】${LOAD}
【稼働時間】${UPTIME}
【コンテナ状態】
${CONTAINERS}
【直近1時間のエラー数】${ERROR_COUNT}件
EOF
)

# OpenClawエージェントに送信
$OPENCLAW_CMD agent --message "$MESSAGE"
