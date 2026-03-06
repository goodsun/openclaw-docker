# 入社手続きマニュアル — bon-soleil Holdings

> このドキュメントはテンプレートです。組織名・人名は bon-soleil Holdings の例です。フォーク時に自社の情報に書き換えてください。

## 新規キャラクター（社員）採用フロー

### Step 1: 企画・承認
1. マスター（CEO）またはHQ（テディ🧸）が採用を決定
2. キャラクターの基本設定を決める
   - 名前、性格、役割、所属事業部

### Step 2: 履歴書作成（プリセットJSON）
1. `HR/profiles/mephi.json` をテンプレートとしてコピー
2. 以下を記入:
   - `name` / `name_ja`: 名前
   - `role`: 役職
   - `division`: 所属事業部
   - `hire_date`: 入社日（YYYY-MM-DD）
   - `character`: キャラクター説明（日本語）
   - `prompt_features`: 画像生成用の外見特徴（英語）
   - `styles`: 衣装バリエーション（最低1つ）
   - `personality`: 性格・口調・キャッチフレーズ
3. `HR/profiles/{name}.json` として保存

### Step 3: 証明写真撮影（キャラシート）
1. プリセットJSONの `prompt_features` + `styles` を使って画像生成
2. `assets/tmp/` に仮出力 → 採用版を `HR/charsheets/{name}/` に配置
3. 最低限 1スタイル、推奨は公式（official）+ 日常（casual）の2枚

### Step 4: 魂の注入（AI配属の場合）
1. `.openclaw/workspace/SOUL.md` にキャラの人格を定義
2. OpenClawインスタンスを接続
3. 初回起動で自己紹介させて人格確認

### Step 5: 配属完了
1. git commit & push
2. staffポータルの人事システム（/characters/）で確認
3. 全社Telegram通知（任意）

---

## チェックリスト

```
[ ] プリセットJSON作成      (HR/profiles/{name}.json)
[ ] キャラシート配置        (HR/charsheets/{name}/)
[ ] SOUL.md編集            (AI配属の場合)
[ ] git commit & push
[ ] staffポータルで確認
```

---

## ドレスコード

- 本社テンプレートには **official（公式）** と **casual（日常）** のみ収録
- 支社ごとの追加衣装は各事業部の判断に委ねる
- 公開コンテンツに使用する場合はTPOに配慮すること

---

*人事部 部長代理: メフィ😈 — bon-soleil Holdings*
