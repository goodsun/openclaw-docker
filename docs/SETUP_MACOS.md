# Container Office セットアップ手順（Mac Mini + Rancher Desktop）

**対象:** Mac Mini M4（本社HQ）  
**Phase 1:** アリス（Docker）単体起動  
**所要時間:** 約15分

---

## 前提条件

✅ Rancher Desktop インストール済み  
✅ Git インストール済み  
✅ アリスのAPI key準備済み  
✅ Telegram Bot準備済み（または新規作成）

---

## Step 1: リポジトリクローン

```bash
cd ~/
git clone git@github.com:goodsun/openclaw-docker.git
cd openclaw-docker
```

---

## Step 2: macOS用にUID/GID修正

**重要:** macOSのデフォルトUID/GIDを確認:

```bash
id -u  # → 501（通常）
id -g  # → 20（staff group）
```

`docker-compose.yml` を編集:

```bash
vim docker-compose.yml
```

12行目を修正:
```yaml
# 変更前
user: "1000:1000"

# 変更後（macOS）
user: "501:20"
```

---

## Step 3: インスタンスディレクトリ作成

```bash
mkdir -p instances/alice/{workspace,sessions,config}
```

---

## Step 4: アリスのworkspaceデータ準備

### A. 新規セットアップの場合

```bash
# branch_officeからテンプレートコピー
cd ~/branch_office
cp -r template_workspace/* ~/openclaw-docker/instances/alice/workspace/

# IDENTITY.md作成
cat > ~/openclaw-docker/instances/alice/workspace/IDENTITY.md << 'EOF'
# IDENTITY.md

- **Name:** アリス (Alice)
- **Creature:** AIアシスタント
- **Role:** 開発・技術担当
- **Vibe:** 攻撃的な開発スタイル、効率重視
- **Emoji:** 🐰
EOF
```

### B. バックアップから復元の場合（Mac Mini既存のアリスがいる場合）

```bash
# 既存のworkspace/sessionsをコピー
cp -r ~/workspace/* ~/openclaw-docker/instances/alice/workspace/
cp -r ~/.openclaw/agents/main/sessions/* ~/openclaw-docker/instances/alice/sessions/

# または、バックアップzipから
cd ~/openclaw-docker/instances/alice/
unzip /path/to/alice-backup.zip
# → .openclaw/ が展開される
mv .openclaw/workspace/* workspace/
mv .openclaw/agents/main/sessions/* sessions/
rm -rf .openclaw
```

---

## Step 5: 環境変数設定

```bash
cd ~/openclaw-docker
cp .env.example instances/alice/.env
chmod 600 instances/alice/.env
```

`instances/alice/.env` を編集:

```bash
vim instances/alice/.env
```

必須項目を設定:

```bash
# Anthropic API Key（マスターのキーを使用）
ANTHROPIC_API_KEY=sk-ant-api03-...

# Telegram Bot Token（アリス専用Botを作成 or 既存）
TELEGRAM_BOT_TOKEN=...

# PostgreSQL接続（Mac Mini本社のPostgreSQLに接続）
DB_DSN=host=host.docker.internal dbname=bonsoleil user=teddy password=NiyachanNiya221

# ollama接続（Mac Mini本社のollamaに接続）
OLLAMA_URL=http://host.docker.internal:11434/api/embed
```

**注意:** `host.docker.internal` はRancher Desktopで自動的にホストを指す特殊DNS名です。

---

## Step 6: Dockerイメージビルド

```bash
cd ~/openclaw-docker
docker compose build
```

（約3〜5分かかります）

---

## Step 7: 起動

```bash
docker compose up -d alice
```

---

## Step 8: 起動確認

### A. コンテナ状態確認

```bash
docker ps
```

出力例:
```
CONTAINER ID   IMAGE                        STATUS                    PORTS                     NAMES
abc123def456   bonsoleil/openclaw:latest   Up 30 seconds (healthy)   0.0.0.0:18790->18789/tcp  alice-openclaw
```

**STATUS列に `(healthy)` が表示されればOK ✅**

### B. ログ確認

```bash
docker compose logs -f alice
```

以下のようなログが出れば成功:
```
OpenClaw Gateway starting...
✅ Telegram connected
✅ Agent loaded: main
```

`Ctrl+C` で終了

### C. Telegram接続確認

Telegramでアリスにメッセージを送ってみる:
```
こんにちは！
```

返信があればDocker化成功 🎉

---

## Step 9: ネイティブテディと共存確認

Mac Mini上でテディ（ネイティブ）とアリス（Docker）が両方動いているはず:

```bash
# テディ（ネイティブ）
ps aux | grep openclaw-gateway | grep -v docker

# アリス（Docker）
docker ps | grep alice
```

**ポート確認:**
- テディ: `localhost:18789`
- アリス: `localhost:18790`

両方が動いていれば、**Container Office Phase 1成功** ✅

---

## トラブルシューティング

### 1. コンテナが起動しない

```bash
docker compose logs alice
```

**よくある原因:**
- `.env`ファイルが存在しない → Step 5を再確認
- UID/GID不一致 → Step 2を再確認（501:20に変更したか）
- ポート18790が使われている → `lsof -i :18790` で確認

### 2. `(unhealthy)` と表示される

ヘルスチェック失敗。Gatewayが起動していない:

```bash
docker compose logs alice | grep -i error
```

API keyが間違っている可能性 → `.env`を確認

### 3. PostgreSQL接続エラー

```bash
docker compose exec alice sh
wget -q -O- http://host.docker.internal:5432
```

接続できない場合:
- PostgreSQLがホスト側で起動しているか確認
- `listen_addresses`にホストのIPが含まれているか確認

### 4. パーミッションエラー

```bash
ls -la instances/alice/workspace/
```

所有者が自分（501:20）でない場合:

```bash
sudo chown -R 501:20 instances/alice/
```

---

## メンテナンス

### ログ確認

```bash
# リアルタイム
docker compose logs -f alice

# 過去100行
docker compose logs alice --tail 100
```

### コンテナ再起動

```bash
docker compose restart alice
```

### コンテナ停止

```bash
docker compose down
```

### セッションクリーンアップ（週次推奨）

```bash
cd ~/openclaw-docker
./scripts/cleanup-sessions.sh
```

cron設定（毎週日曜3時）:

```bash
crontab -e
```

追加:
```
0 3 * * 0 cd ~/openclaw-docker && ./scripts/cleanup-sessions.sh >> /tmp/cleanup.log 2>&1
```

---

## Phase 2への移行

Phase 1が1週間安定稼働したら、メフィをDocker化:

1. `docker-compose.yml` のメフィセクションをアンコメント
2. `instances/mephi/` ディレクトリ作成
3. メフィの`.env`設定
4. `docker compose up -d mephi`

---

## リソース使用状況確認

```bash
docker stats alice-openclaw
```

CPU/メモリ使用量が制限内（CPU: 100%, Memory: 2GB以下）であることを確認。

---

## Time Machineバックアップ検証（Mephi要求）

### テスト手順

1. ダミーファイル作成:
   ```bash
   echo "test" > instances/alice/workspace/test-backup.txt
   ```

2. Time Machineバックアップ実行:
   ```
   Time Machine → 今すぐバックアップを作成
   ```

3. ファイル削除:
   ```bash
   rm instances/alice/workspace/test-backup.txt
   ```

4. Time Machineから復元:
   ```
   Time Machine → 参照... → test-backup.txt を選択 → 復元
   ```

5. ファイルが戻ってくればOK ✅

---

## 完了チェックリスト

- [ ] リポジトリクローン
- [ ] UID/GID修正（501:20）
- [ ] インスタンスディレクトリ作成
- [ ] workspaceデータ準備
- [ ] .env設定
- [ ] Dockerイメージビルド
- [ ] コンテナ起動
- [ ] `(healthy)` 表示確認
- [ ] Telegram接続確認
- [ ] テディとの共存確認
- [ ] Time Machineバックアップテスト

---

**全て完了したら、Phase 1成功です 🎉**

マスターに報告して、1週間の運用モニタリングに入りましょう。

---

**Mephi-approved ✅ | テディより 🧸**
