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

### ⚠️ labo_portal の共有マウントと環境変数の優先順位

`~/labo_portal` を全インスタンスで共有マウントしているため、
`~/labo_portal/.env` はHQ（テディ）用の設定が入っている。

labo_portal は `dotenv` を使っており、**環境変数（コンテナenv）が .env より優先される**。
そのため、インスタンス固有の設定は必ず `instances/<name>/.env` に記載すること。

**必須の上書き項目：**

```env
APP_BASE=/<name>              # labo_portalのベースパス
LABO_PORT=8800                # ポート（HQは8801なので別にする）
LABO_NAME=<name> labo-portal  # ポータル名
LABO_AGENT=<AIの名前>         # ログイン画面に表示される名前
WORKSPACE_ROOT=/home/node/.openclaw/workspace  # データ保存先
LABO_SECRET=<ランダム文字列>  # セッション署名キー（HQと別にしないとCookieが共有される）
LABO_PASSWORD=<パスワード>    # ログインパスワード
```

> ❌ `LABO_SECRET` を共有にすると、異なるインスタンス間でセッションCookieが有効になる
> ❌ `LABO_PASSWORD` を設定しないとHQのパスワードが使われる
> ✅ 実際に有効なパスワードは **環境変数に設定した値**（.envの値は無視される）

### labo_portal の data ディレクトリ

`WORKSPACE_ROOT/data/` 配下にプラグインデータが保存される：

```
workspace/data/
  presets/          ← image_genのモデル・タッチプリセット
  casts/            ← キャラクタープロファイル
  docs/             ← ドキュメント・下書き
  generated/        ← 生成画像
  scenes/           ← シーン画像
```

`docker-compose.yml` で `workspace/data` をインスタンス別ボリュームにマウントすること：

```yaml
volumes:
  - ./<name>_data:/home/node/.openclaw/workspace/data
```

> ⚠️ 旧構造の `labo_portal/data/image_gen/` は廃止済み。`workspace/data/presets/` が正しい場所。

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

---

## インスタンスの設定を変更したい場合

コンテナの環境変数は**起動時に固定**される。
コンテナ内でsourceしてもopenclaw/labo_portalのプロセスには反映されない。

### 変更手順（ホスト側で作業）

```bash
# 1. 設定を編集
vi ~/openclaw-docker/instances/<name>/.env

# 2. コンテナを再起動
cd ~/openclaw-docker
docker compose up -d <name>
```

### AIインスタンス自身が設定変更を依頼する場合

みぃちゃん等のAIが設定変更を希望する場合：
1. AI が変更内容をオーナーまたはテディに伝える
2. ホスト側で `instances/<name>/.env` を編集
3. `docker compose up -d <name>` で再起動

> AIはコンテナ内からは自分の環境変数を変更できない。
> 変更はホスト側の作業が必須。
