# openclaw-docker

bon-soleil Holdings — Container Office  
**Mephi-approved configuration (95/100)**

OpenClawインスタンスをDockerコンテナ化し、複数AIの安全な共存環境を提供します。

---

## 特徴

- ✅ **環境分離:** 各AIが独立したコンテナで動作
- ✅ **セキュリティ:** 非rootユーザー実行、専用ネットワーク
- ✅ **リソース管理:** CPU/メモリ制限、ログローテーション
- ✅ **ポータビリティ:** イメージ + ボリュームでどこでも実行可能

---

## Phase 1: アリス（PoC）

### 前提条件

- Docker Desktop (macOS) or Docker Engine (Linux)
- OpenClaw API key (Anthropic)
- Telegram Bot Token

### セットアップ

#### 1. リポジトリクローン

```bash
git clone git@github.com:goodsun/openclaw-docker.git
cd openclaw-docker
```

#### 2. インスタンスセットアップ（推奨）

セキュアなセットアップスクリプトを使用:

```bash
./scripts/setup-instance.sh alice
```

これにより以下が自動実行されます:
- ディレクトリ作成（`instances/alice/{workspace,sessions,config}`）
- `.env`ファイル作成（`.env.example`からコピー）
- **パーミッション設定（`chmod 600`）**

#### 3. 環境変数設定

`.env`ファイルを編集:

```bash
vim instances/alice/.env
```

必須項目を設定:

**UID/GID（重要）:**

macOSとLinuxでUID/GIDが異なるため、現在の環境を確認して設定:

**macOS:**
```bash
id -u  # 通常 501
id -g  # 通常 20（staff）
```

```bash
# instances/alice/.env
CONTAINER_UID=501
CONTAINER_GID=20
```

**Linux:**
```bash
id -u  # 通常 1000
id -g  # 通常 1000
```

```bash
# instances/alice/.env
CONTAINER_UID=1000
CONTAINER_GID=1000
```

**APIキー等:**
- `ANTHROPIC_API_KEY`: https://console.anthropic.com/settings/keys で取得（**必須**）
- `TELEGRAM_BOT_TOKEN`: @BotFather で `/newbot` して取得（**オプション** — 設定しない場合はTUI/WebChatのみ）

⚠️ **注意**: `docker-compose.yml`を直接編集しないでください。`.env`で設定します。

#### 4. workspaceセットアップ

```bash
# SOUL.md, USER.md等をinstances/alice/workspace/に配置
# または、バックアップzipから復元
cd instances/alice
unzip /path/to/alice-backup.zip
```

#### 5. イメージビルド

```bash
docker-compose build
```

#### 6. 起動

```bash
docker-compose up -d alice
```

#### 7. ログ確認

```bash
docker-compose logs -f alice
```

#### 8. ヘルスチェック

```bash
docker ps
# STATUS列に "(healthy)" が表示されればOK
```

---

## メンテナンス

### セッションクリーンアップ（Mephi requirement）

30日以前のセッションファイルを削除:

```bash
./scripts/cleanup-sessions.sh
```

cron設定例（週次実行）:

```bash
# crontab -e
0 3 * * 0 cd /path/to/openclaw-docker && ./scripts/cleanup-sessions.sh
```

### ログ確認

```bash
# リアルタイム
docker-compose logs -f alice

# 過去ログ
docker logs alice-openclaw
```

### コンテナ再起動

```bash
docker-compose restart alice
```

### イメージ更新

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Mephi承認条件（Phase 1）

- ✅ UID/GID設計（`user: "1000:1000"`）
- ✅ 専用ネットワーク（`alice-net`）
- ✅ 機密情報管理（`.env` + `.gitignore`）
- ✅ リソース制限（CPU 1コア、メモリ2GB）
- ✅ ヘルスチェック（`healthcheck`）
- ✅ ログローテーション（`logging`）
- ✅ セッション削除スクリプト（`cleanup-sessions.sh`）
- ⏳ Time Machineバックアップ検証（Phase 1中）

---

## Phase 2: メフィ追加

Phase 1が1週間安定稼働したら、`docker-compose.yml`のメフィセクションをアンコメント:

```bash
docker-compose up -d mephi
```

---

## トラブルシューティング

### コンテナが起動しない

```bash
docker-compose logs alice
```

よくある原因:
- `.env`ファイルが存在しない → `./scripts/setup-instance.sh alice` で作成
- UID/GID不一致 → `instances/alice/.env` の `CONTAINER_UID/CONTAINER_GID` を確認
- ポート競合 → `18790`が使われていないか確認

### パーミッションエラー

```bash
# ホスト側のディレクトリ所有者を確認
ls -la instances/alice/

# 必要に応じて所有者変更（macOS）
sudo chown -R 501:20 instances/alice/

# 必要に応じて所有者変更（Linux）
sudo chown -R 1000:1000 instances/alice/
```

### ヘルスチェック失敗

Gatewayが起動していない可能性。ログを確認:

```bash
docker-compose logs alice | grep -i error
```

---

## ディレクトリ構造

```
openclaw-docker/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── scripts/
│   └── cleanup-sessions.sh
└── instances/
    ├── alice/
    │   ├── .env           # git管理外
    │   ├── workspace/
    │   ├── sessions/
    │   └── config/
    └── mephi/             # Phase 2
        ├── .env
        ├── workspace/
        ├── sessions/
        └── config/
```

---

## コンテナ間通信（跨ぎ sessions_send）

### 仕組み
`sessions_send` ツールは**同一Gateway内のセッションにしか送れない**。
別コンテナのAIに送るには `/tools/invoke` エンドポイントをHTTP直叩きする。

### ホストOS（テディ）→ コンテナへの送信例

```bash
# みぃちゃんのセッション一覧を取得
curl -X POST http://127.0.0.1:18790/tools/invoke \
  -H "Authorization: Bearer mie-dev-token-2026" \
  -H "Content-Type: application/json" \
  -d '{"tool":"sessions_list","args":{}}'

# みぃちゃんへメッセージ送信
curl -X POST http://127.0.0.1:18790/tools/invoke \
  -H "Authorization: Bearer mie-dev-token-2026" \
  -H "Content-Type: application/json" \
  -d '{"tool":"sessions_send","args":{"sessionKey":"agent:main:main","message":"テディからみぃちゃんへ！"}}'
```

### ポイント
- **ホストから**はポートマッピングで直接届く（`shared-agents` ネットワーク不要）
- **コンテナ内から別コンテナへ**送る場合は `shared-agents` ネットワークが必要
- 受信側の `openclaw.json` に以下が必須:

```json
"gateway": {
  "tools": { "allow": ["sessions_send"] },
  "auth": { "mode": "token", "token": "your-token" }
}
```

### 実証済み（2026-03-07）
テディ（ホストOS）→ みぃちゃん（コンテナ）跨ぎ通信成功 🎉

---

## ライセンス

Private repository — bon-soleil Holdings internal use only

---

**Mephi-approved 98/100 ✅ | Mac Mini M4 稼働中 🚀**
