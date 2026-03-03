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

#### 2. インスタンスディレクトリ作成

```bash
mkdir -p instances/alice/{workspace,sessions,config}
```

#### 3. 環境変数設定

```bash
cp .env.example instances/alice/.env
chmod 600 instances/alice/.env

# エディタで編集
vim instances/alice/.env
```

必須項目:
- `ANTHROPIC_API_KEY`
- `TELEGRAM_BOT_TOKEN`

#### 4. workspaceセットアップ

```bash
# SOUL.md, USER.md等をinstances/alice/workspace/に配置
# または、バックアップzipから復元
cd instances/alice
unzip /path/to/alice-backup.zip
```

#### 5. UID/GID確認（重要）

**macOS:**
```bash
id -u  # 通常 501
id -g  # 通常 20（staff）
```

**Linux:**
```bash
id -u  # 通常 1000
id -g  # 通常 1000
```

`docker-compose.yml` の `user: "1000:1000"` を環境に合わせて修正:

```yaml
# macOSの場合
user: "501:20"

# Linuxの場合
user: "1000:1000"
```

#### 6. イメージビルド

```bash
docker-compose build
```

#### 7. 起動

```bash
docker-compose up -d alice
```

#### 8. ログ確認

```bash
docker-compose logs -f alice
```

#### 9. ヘルスチェック

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
- `.env`ファイルが存在しない → `.env.example`をコピー
- UID/GID不一致 → `docker-compose.yml`の`user:`を確認
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

## ライセンス

Private repository — bon-soleil Holdings internal use only

---

**Mephi-approved ✅ | Phase 1 ready 🚀**
