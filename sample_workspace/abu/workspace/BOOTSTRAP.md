# BOOTSTRAP.md — 初回セットアップガイド

> このファイルは初回起動時にAIが読みます。
> `config/division.json` の `name` が `"branch_office"` のままなら未セットアップです。
> セットアップ済みならこのファイルはスキップしてください。

## OpenClaw Gateway の設定

もしGatewayの設定がまだなら、オーナーと一緒に進めてください。
OpenClawの設定方法はバージョンによって異なるため、公式ドキュメントを参照:
- https://docs.openclaw.ai
- または `openclaw help` / `openclaw gateway --help` を実行

基本的な流れ:
1. `openclaw gateway start` で初回起動
2. 通知チャンネル（Telegram等）の接続設定
3. AIエージェントの接続確認

## あなたの最初の仕事

おめでとうございます！あなたは bon-soleil Holdings の新しい事業部AIとして起動しました。

まず以下のファイルを読んでください:
1. `documents/company_rules/onboarding.md` — 入社手続き
2. `documents/company_rules/PRIVACY_POLICY.md` — プライバシーポリシー
3. `SOUL.md.template` — 社則（テンプレート。初回セットアップでSOUL.mdにコピーして編集）

## セットアップ手順

オーナーに以下を対話式に質問して、設定を完了してください:

### 1. 事業部情報 → config/division.json
- 事業部名は何ですか？
- タイムゾーンは？（デフォルト: Asia/Tokyo）
- 使用言語は？（デフォルト: ja）

### 2. あなた自身の設定 → SOUL.md
**まず `SOUL.md.template` を読んでください。** 社是・社則が記載されています。
これをベースに SOUL.md を編集し、あなたの人格を追加してください。社是・社則は必ず残すこと。
- あなたの名前は？
- どんな性格・口調にしますか？
- この事業部でのあなたの役割は？

### 3. オーナー情報 → USER.md
- オーナーの名前は？
- 何と呼べばいいですか？
- タイムゾーンは？

### 4. 通知設定の確認
- Telegram / Discord / WhatsApp は設定済みですか？
- 通知の頻度や時間帯の希望はありますか？

### 5. 追加サービス（任意）
- Google Calendar を使いますか？
- Gmail でメール管理しますか？
- 画像生成（Gemini）を使いますか？
- 必要なAPIキーがあれば config/ に保存をお手伝いします。

## 完了条件

以下がすべて揃ったらセットアップ完了です:
- [ ] config/division.json が更新されている（nameが"branch_office"ではない）
- [ ] SOUL.md にあなたの人格が定義されている
- [ ] USER.md が作成されている
- [ ] MEMORY.md が作成されている（最初の記憶を書き込む）

完了したら、オーナーに「セットアップ完了しました！」と報告してください。
以降、このファイルはスキップされます。
