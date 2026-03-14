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
│   │   ├── generated/         # 生成画像の一時置き場
│   │   └── uploads/           # アップロードファイル
│   ├── casts/                 # キャラクターシート画像
│   ├── docs/                  # ドキュメント・ドラフト
│   │   ├── draft/             # 下書き置き場
│   │   └── discussion/        # ディスカッション等
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

### テディ（HQ: /Users/teddy/workspace/）✅ 完了済み

### アリス・彰子さん — Hetzner 新規環境（alice-hetzner）

**新規環境なのでブルーグリーン不要。workspaceはbase_wsからclone済み。**

#### 1. EC2側の古い設定を持ってくる（SSH接続して実行）

```bash
# EC2にSSH接続して、今のopenclaw設定を確認
ssh alice  # または bizeny
cat ~/.openclaw/openclaw.json
```

必要な情報をメモ：
- Telegram Bot Token
- Anthropic API Key
- Gemini API Key

#### 2. Hetznerにopenclaw configureを実行

```bash
ssh alice@157.180.42.159   # アリスの場合
# または
ssh bizeny@157.180.42.159  # 彰子さんの場合

openclaw configure
```

対話形式で以下を設定：
- AI プロバイダー（Anthropic / Gemini）
- Telegram Bot Token
- `agents.defaults.workspace: /home/alice/workspace`（または `/home/bizeny/workspace`）
- `gateway.mode: local`

#### 3. Gemini APIキーをworkspaceに保存

```bash
mkdir -p ~/workspace/config/google
echo "YOUR_GEMINI_API_KEY" > ~/workspace/config/google/gemini_api_key
```

#### 4. SOUL.md・IDENTITY.md・USER.mdを編集

`/srv/shared/base_ws` のテンプレートが入っているので、自分用に書き換える。

#### 5. systemdサービスとして登録

```bash
# rootで実行（sudoで）
sudo tee /etc/systemd/system/openclaw-alice.service << EOF
[Unit]
Description=OpenClaw Gateway (Alice)
After=network.target

[Service]
Type=simple
User=alice
WorkingDirectory=/home/alice/workspace
Environment=HOME=/home/alice
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/local/bin/openclaw gateway
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable openclaw-alice
sudo systemctl start openclaw-alice
sudo systemctl status openclaw-alice
```

#### 6. EC2側の古いサービスを停止

Hetzner側が安定したら、EC2のopenclaw gatewayを停止。

```bash
# EC2側
sudo systemctl stop openclaw-gateway
sudo systemctl disable openclaw-gateway
```

---

## 注意事項

- **workspace は git 管理禁止** — MEMORY.md・config/ 等に個人情報・APIキーが含まれるため。`git init` しないこと。`config/google/gemini_api_key` 等のAPIキーはこの前提の上で workspace 内に置いている。
- **`node_modules/` は workspace 直下に置かない** — 各プロジェクト内部に閉じること
- **APIキーはファイルに保存** — `config/google/gemini_api_key` 等へ
- **`data/generated/` の画像は使用後削除** — 溜めない
- **退避先は `~/nouse/`** — trash ではなくマスターが後で確認して消す場所
