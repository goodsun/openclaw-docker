# Workspace 構成ガイド

> アブーが確立した標準構成（2026-03-14）。各AIはこれに合わせること。

---

## 標準ディレクトリ構成

```
workspace/
├── AGENTS.md          # 行動原則・ルール（branch_officeテンプレートから）
├── BOOTSTRAP.md       # 初回セットアップガイド（初回読んだら消してOK）
├── HEARTBEAT.md       # ハートビート設定（空でOK）
├── IDENTITY.md        # 自分の名前・キャラ定義
├── SOUL.md            # 人格・価値観（自分で育てる）
├── SOUL.md.template   # SOULのベーステンプレート（参考用）
├── TOOLS.md           # ツール・コマンドメモ
├── USER.md            # オーナー情報
│
├── config/
│   ├── division.json          # 事業部設定
│   └── google/
│       └── gemini_api_key     # Gemini APIキー
│
├── data/
│   ├── assets/
│   │   ├── generated/         # 生成画像（SNS投稿後は削除）
│   │   └── uploads/           # アップロードファイル
│   ├── casts/                 # キャラクターシート画像
│   │   └── {キャラ名}/
│   ├── docs/                  # ドキュメント・ドラフト
│   ├── generated/             # labo_portal の画像生成出力先
│   ├── presets/               # モデルプリセット設定
│   └── scenes/                # シーン素材
│
├── logs/                      # サービスログ
│   ├── chat-api.log
│   ├── chat-api.err.log
│   └── ...
│
├── memory/                    # 日次メモリファイル
│   ├── .gitkeep
│   └── YYYY-MM-DD.md
│
├── projects/                  # 各AIが管理するプロジェクト
│   ├── .gitkeep
│   └── labo_portal/           # ← git clone して自分でビルド・起動
│
├── scripts/                   # スクリプト置き場
│   ├── .gitkeep
│   ├── common/
│   │   ├── cleanup_tmp.sh
│   │   └── sync.sh
│   └── samples/
│
└── skills/                    # スキル置き場
    ├── nanobanana/
    │   └── SKILL.md
    ├── rag-ingest/
    │   └── SKILL.md
    └── rag-search/
        └── SKILL.md
```

---

## 各AIがやること（初回セットアップ）

### 1. nouse/ に移す（古いディレクトリ）

以前のworkspaceパスが `.openclaw/workspace` だった場合、不要なものを整理する：

```bash
# 古いworkspaceデータが残っていたら nouse/ へ
mkdir -p ~/nouse
mv ~/.openclaw/workspace ~/nouse/openclaw_workspace_old
```

また、workspace内の不要ファイルも整理：
```bash
# .npm-cache は不要
rm -rf ~/workspace/.npm-cache

# .DS_Store は不要
find ~/workspace -name ".DS_Store" -delete

# workspace内の .git は禁止（workspaceはgit管理しない）
# ある場合は rm -rf ~/workspace/.git
```

### 2. 不足ディレクトリを作成

```bash
mkdir -p ~/workspace/config/google
mkdir -p ~/workspace/data/{assets/generated,assets/uploads,casts,docs,generated,presets,scenes}
mkdir -p ~/workspace/logs
mkdir -p ~/workspace/memory
mkdir -p ~/workspace/projects
mkdir -p ~/workspace/scripts/{common,samples,tests}
mkdir -p ~/workspace/skills
touch ~/workspace/memory/.gitkeep
touch ~/workspace/projects/.gitkeep
touch ~/workspace/scripts/.gitkeep
```

### 3. labo_portal のセットアップ

```bash
cd ~/workspace/projects
git clone https://github.com/goodsun/labo_portal.git
cd labo_portal
npm install
npm run build

# .env を作成（APP_BASE は各自の設定に合わせる）
cat > .env << EOF
LABO_NAME=labo-portal
LABO_AGENT=（自分の名前）
LABO_PASSWORD=（任意のパスワード）
LABO_SECRET=（ランダム文字列）
LABO_PORT=8800
APP_BASE=/（自分のベースパス）
GEMINI_API_KEY=（Gemini APIキー）
EOF

# 起動
node dist/app.js &
```

### 4. config を整備

```bash
# division.json
cat > ~/workspace/config/division.json << EOF
{
  "name": "（事業部名）",
  "timezone": "Asia/Tokyo",
  "language": "ja"
}
EOF

# Gemini APIキー
echo "（APIキー）" > ~/workspace/config/google/gemini_api_key
```

---

## 注意事項

- **workspace に `.git` を作らない** — MEMORY.md 等に個人情報が含まれるため
- **APIキーはファイルに保存** — 環境変数や .env ではなく `config/google/gemini_api_key` 等に
- **`.npm-cache/` は workspace に入れない** — `.gitignore` 対象だが、そもそも作らないよう注意
- **`data/generated/` の画像は使用後削除** — 溜めない

---

## 各インスタンスの現状と作業内容

| AI | workspace | 状態 | やること |
|---|---|---|---|
| アブー | `instances/abu/workspace` | ✅ 完成形 | — |
| メフィ | `instances/mephi/workspace` | ⚠️ 不完全 | ①`.git`を削除 ②不足ディレクトリを作成 ③labo_portal をビルド |
| みぃ | `instances/mie/workspace` | ❌ なし | ①workspaceディレクトリを作成 ②全ディレクトリを作成 ③labo_portal をビルド |
