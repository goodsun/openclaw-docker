# 新規インスタンスセットアップ手順

> 初号試験（mie）の結果として確立した手順。2026-03-10

---

## 概要

openclaw-dockerで新しいAIインスタンスを立ち上げる手順。
token類を `.env` に書いて `docker compose up` するだけで動く状態を目指す。

---

## 1. sample_workspace を整備する

`sample_workspace/<name>/` がそのインスタンスの「初期値テンプレート」になる。

```
sample_workspace/<name>/
  SOUL.md       ← 性格・振る舞いのルール
  IDENTITY.md   ← 名前・誕生日・家族関係など
  AGENTS.md     ← ワークスペースのルール
  USER.md       ← オーナー情報
  TOOLS.md      ← ツール固有情報
  HEARTBEAT.md  ← ハートビート設定
```

### IDENTITY.md の書き方

```markdown
# IDENTITY.md - Who Am I?

- **Name:** <名前>
- **Creature:** AIアシスタント
- **Vibe:** <性格の一言>
- **Emoji:** <絵文字>
- **Birthday:** <誕生日>

## 家族関係
- **オーナー:** <オーナー名>
```

> ⚠️ フルネーム・Telegram IDなどの個人情報は書かない。
> `sample_workspace/*/memory/` は `.gitignore` で除外済み。

---

## 2. instances/<name>/ を作成する

```bash
mkdir -p ~/openclaw-docker/instances/<name>
```

### .env を作成する

```bash
cat > ~/openclaw-docker/instances/<name>/.env << EOF
CONTAINER_UID=501
CONTAINER_GID=20
TZ=Asia/Tokyo
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=...
GEMINI_API_KEY=...
EOF
chmod 600 ~/openclaw-docker/instances/<name>/.env
```

### workspace を sample_workspace からコピーする

```bash
cp -r ~/openclaw-docker/sample_workspace/<name> \
      ~/openclaw-docker/instances/<name>/workspace
```

### labo_portal ディレクトリを作成する（パーミッション対策）

```bash
mkdir -p ~/openclaw-docker/instances/<name>/labo_portal
```

---

## 3. docker-compose.yml にサービスを追加する

```yaml
<name>:
  build: .
  image: bonsoleil/openclaw:latest
  container_name: <name>-openclaw
  user: "${CONTAINER_UID:-1000}:${CONTAINER_GID:-1000}"
  volumes:
    - ./instances/<name>/.openclaw:/home/node/.openclaw
    - ./instances/<name>/workspace:/home/node/.openclaw/workspace
    - ./instances/<name>/labo_portal:/home/node/labo_portal
  ports:
    - "<port>:18789"
  networks:
    - shared-agents
  restart: on-failure
  env_file:
    - ./instances/<name>/.env
  environment:
    - TZ=Asia/Tokyo
  mem_limit: 2g
  cpus: 1.0
  healthcheck:
    test: ["CMD", "wget", "--spider", "-q", "http://localhost:18789/health"]
    interval: 30s
    timeout: 5s
    retries: 3
    start_period: 10s
```

---

## 4. 起動する

```bash
cd ~/openclaw-docker
docker compose up -d <name>
docker logs <name>-openclaw --follow
```

起動ログにこれが出れば成功：

```
📦 labo_portal をクローン中...
✅ labo_portal クローン完了
[gateway] listening on ws://127.0.0.1:18789
[telegram] starting provider (@<bot_name>)
```

---

## 注意点

### labo_portal のパーミッション問題

コンテナ内の `/home/node/` は `node` ユーザー所有。
UID 501 で動作する場合、ボリュームマウントなしでは書き込めない。
→ **必ず `instances/<name>/labo_portal/` をマウントすること。**

### restart: on-failure の連続リトライ

entrypoint が失敗すると `on-failure` で何度もリトライする。
起動ログで原因を確認してから修正する。

```bash
docker logs <name>-openclaw 2>&1 | tail -20
```

### openclaw.json の自動生成

初回起動時に `entrypoint.sh` が `openclaw setup` を実行して
`instances/<name>/.openclaw/openclaw.json` を自動生成する。
手動で作る必要はない。

---

## クリーンインストールし直す場合

```bash
docker compose stop <name>
docker compose rm -f <name>
rm -rf instances/<name>/.openclaw
rm -rf instances/<name>/workspace
rm -rf instances/<name>/labo_portal
cp -r sample_workspace/<name> instances/<name>/workspace
mkdir -p instances/<name>/labo_portal
docker compose up -d <name>
```

---

*初号試験: mie（2026-03-10）*
*文責: テディ🧸*
