# 新しいAIインスタンスのセットアップ手順

bon-soleil Container Officeで新しいAIインスタンスを追加する手順。

## 概要

各AIインスタンスは独立したDockerコンテナとして動作する。
- **workspace** — SOUL.md / IDENTITY.md / MEMORY.md などの人格・記憶ファイル
- **sessions** — OpenClawのセッションJSONL（会話履歴）
- **config** — 認証情報など

---

## Phase 1: インスタンスを立ち上げる

### 1. ディレクトリ作成

```bash
mkdir -p instances/<name>/.openclaw
```

### 2. .env を作成

```bash
cp instances/mephi_dev_backup/.env.example instances/<name>/.env
# ANTHROPIC_API_KEY を記入
chmod 600 instances/<name>/.env
```

### 3. sample_workspace をコピー

```bash
cp -r sample_workspace/mephi sample_workspace/<name>
```

`sample_workspace/<name>/` 以下を編集する：

| ファイル | 内容 |
| --- | --- |
| `SOUL.md` | キャラクターの魂・哲学・行動原則 |
| `IDENTITY.md` | 名前・外見・役職・口調 |
| `USER.md` | マスターの情報 |
| `AGENTS.md` | 起動時の読み込みルール（共通テンプレート） |
| `TOOLS.md` | 環境固有のメモ |

### 4. docker-compose.yml にサービス追加

```yaml
  <name>:
    build: .
    image: bonsoleil/openclaw:latest
    container_name: <name>-openclaw
    user: "${CONTAINER_UID:-1000}:${CONTAINER_GID:-1000}"
    volumes:
      - ./instances/<name>/.openclaw:/home/node/.openclaw
      - ./sample_workspace/<name>:/home/node/.openclaw/workspace
    ports:
      - "18792:18789"   # ポートは被らないように
    networks:
      - <name>-net
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

networks:
  <name>-net:
    driver: bridge
```

### 5. 起動

```bash
~/.rd/bin/docker compose up -d <name>
```

### 6. TUIで接続・初回起動確認

コンテナに入ってTUIを立ち上げる：

```bash
~/.rd/bin/docker compose exec <name> bash
openclaw tui
```

AIが自己紹介して、SOUL.mdを読んでいれば成功。

---

## Phase 2: 記憶を注入する

→ [MEMORY_INJECTION.md](./MEMORY_INJECTION.md) を参照。

---

## ポート割り当て一覧

| インスタンス | ポート |
| --- | --- |
| alice | 18790 |
| mephi | 18791 |
| (次の子) | 18792 |
