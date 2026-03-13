# Workspace 構成ガイド

> アブーが確立した標準構成（2026-03-14）。各AIはこれに合わせること。

---

## 標準ディレクトリ構成

```
workspace/
├── AGENTS.md              # 行動原則・ルール
├── BOOTSTRAP.md           # 初回セットアップガイド（初回読んだら消してOK）
├── HEARTBEAT.md           # ハートビート設定
├── IDENTITY.md            # 自分の名前・キャラ定義
├── SOUL.md                # 人格・価値観（自分で育てる）
├── SOUL.md.template       # SOULのベーステンプレート（参考用）
├── TOOLS.md               # ツール・コマンドメモ
├── USER.md                # オーナー情報
│
├── config/
│   ├── division.json          # 事業部設定
│   └── google/
│       └── gemini_api_key     # Gemini APIキー
│
├── data/
│   ├── assets/
│   │   ├── generated/         # 生成画像の一時置き場（使ったら削除）
│   │   └── uploads/           # アップロードファイル
│   ├── casts/                 # キャラクターシート画像
│   ├── docs/                  # ドキュメント・ドラフト
│   ├── generated/             # labo_portal 画像生成出力
│   ├── presets/               # モデルプリセット設定
│   └── scenes/                # シーン素材
│
├── logs/                      # サービスログ
├── memory/                    # 日次メモリファイル（YYYY-MM-DD.md）
├── projects/                  # 各AIが管理するプロジェクト
│   └── labo_portal/           # ← git clone して自分でビルド・起動
├── scripts/                   # スクリプト置き場
└── skills/                    # スキル置き場
```

**workspaceに置かないもの:**
- `.git/` — workspace は git 管理禁止（個人情報漏洩リスク）
- `node_modules/` — プロジェクト内部に閉じること
- `documents/` — workspace 外（`~/documents/` 等）に置く
- 画像ファイルの直置き — 必ず `data/` 配下へ

---

## A. コンテナ版（メフィ向け）

**ブルーグリーン方式**: 丸ごと退避してから新規作成。

```bash
# 1. 古いworkspaceを退避
mkdir -p ~/nouse
mv ~/workspace ~/nouse/workspace_$(date +%Y%m%d_%H%M%S)

# 2. 標準構成を作成
mkdir -p ~/workspace
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

# 3. 設定ファイルを復元（nouseから必要なものだけ持ってくる）
# AGENTS.md / SOUL.md / IDENTITY.md / TOOLS.md / USER.md / MEMORY.md など

# 4. labo_portal のセットアップ
cd ~/workspace/projects
git clone https://github.com/goodsun/labo_portal.git
cd labo_portal
npm install && npm run build
# .env を作成して起動
```

---

## B. ホスト直置き版（テディ・アリス・彰子さん向け）

**段階的整理**: 壊さずに不足を補い、余分を nouse/ へ逃がす。

### テディ（HQ: /Users/teddy/workspace/）

**やること:**
```bash
# 不足ディレクトリを追加
mkdir -p ~/workspace/config/google
mkdir -p ~/workspace/data/{assets/generated,assets/uploads,presets}
mkdir -p ~/workspace/logs

# SOUL.md.template を追加（branch_office テンプレートからコピー）

# scripts/.git を削除（workspaceのgit管理禁止）
rm -rf ~/workspace/scripts/.git

# 画像直置きを nouse へ
mkdir -p ~/nouse/workspace_images
mv ~/workspace/*.jpg ~/workspace/*.png ~/nouse/workspace_images/ 2>/dev/null

# documents/ は workspace 外へ（~/documents/ に移動 or そのまま維持）
```

### アリス（EC2 alice: ~/workspace/）

**現状:** ほぼ空（`projects/` に既存プロジェクトのみ）

```bash
# 標準ディレクトリを追加
mkdir -p ~/workspace/config/google
mkdir -p ~/workspace/data/{assets/generated,assets/uploads,casts,docs,generated,presets,scenes}
mkdir -p ~/workspace/logs
mkdir -p ~/workspace/memory
mkdir -p ~/workspace/scripts/{common,samples,tests}
mkdir -p ~/workspace/skills
touch ~/workspace/memory/.gitkeep
touch ~/workspace/scripts/.gitkeep

# AGENTS.md / SOUL.md / IDENTITY.md / TOOLS.md / USER.md / HEARTBEAT.md を作成
```

### 彰子さん（EC2 bizeny: ~/workspace/）

**現状:** かなり整ってる。`node_modules/` が workspace 直下に生えているのを退避するだけ。

```bash
# node_modules を nouse へ（workspace直下に置くのはNG）
mkdir -p ~/nouse
mv ~/workspace/node_modules ~/nouse/workspace_node_modules_$(date +%Y%m%d)

# SOUL.md.template が trash/ にあるので workspace/ に移動
cp ~/workspace/trash/SOUL.md.template ~/workspace/SOUL.md.template

# 不足確認（logs/ はある、memory/ はある → ほぼOK）
```

---

## 注意事項

- **workspace に `.git` を作らない** — MEMORY.md 等に個人情報が含まれるため
- **`node_modules/` は workspace 直下に置かない** — 各プロジェクト内部に閉じること
- **APIキーはファイルに保存** — `config/google/gemini_api_key` 等へ
- **`data/generated/` の画像は使用後削除** — 溜めない
- **退避先は `~/nouse/`** — trash ではなくマスターが後で確認して消す場所
