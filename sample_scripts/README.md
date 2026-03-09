# sample_scripts — OpenClaw 活用サンプル集

「こう使えるのか」がわかるサンプルスクリプト集。
本番投入前に動作確認・カスタマイズして使うこと。

---

## daily_report.sh — デイリーシステムレポート

Linuxのcronからシェルスクリプトを叩き、
システム状況をOpenClawエージェントがTelegramへ報告する。

### ポイント

```
Linux cron
  ↓ daily_report.sh を定刻実行
  ↓ df / free / docker ps でシステム情報を収集
  ↓ openclaw agent --message "..." でエージェントに依頼
OpenClawエージェント
  ↓ 情報を整形してレポート作成
  ↓ その日にふさわしい一言を添える
Telegram
  ↓ 受信
```

**シェルが「集める」、エージェントが「考えて送る」** のが肝。

### セットアップ

```bash
# 1. スクリプトを配置
cp daily_report.sh /usr/local/bin/
chmod +x /usr/local/bin/daily_report.sh

# 2. crontabに登録（毎朝9時）
crontab -e
# 以下を追加:
# 0 9 * * * /usr/local/bin/daily_report.sh >> /var/log/daily_report.log 2>&1

# 3. 手動で動作確認
/usr/local/bin/daily_report.sh
```

### カスタマイズ例

- 報告時刻を変える → crontabの時刻を調整
- 報告内容を変える → スクリプト内の変数を追加・削除
- 複数エージェントに送る → `openclaw agent --agent mephi` のように対象を指定
- AI不要なタスクと混在させる → 同じcronスクリプト内にまとめて管理

---

*bon-soleil Holdings — Reviewed by Mephi 😈*
