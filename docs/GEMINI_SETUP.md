# Gemini（Google）バックエンドでの動かし方

AnthropicではなくGoogle Geminiを使ってAIインスタンスを動かす手順。
ひのちゃんマシンのりんちゃん（2026-03-05検証済み）。

---

## 1. auth-profiles.json の設定

Gemini APIキーはOpenClawの`auth-profiles.json`で管理される。
**`openclaw.json`の`auth.profiles`にはAPIキーを書かない**（フォーマットエラーになる）。

```bash
mkdir -p instances/<name>/.openclaw/agents/main/agent
```

```json
// instances/<name>/.openclaw/agents/main/agent/auth-profiles.json
{
  "version": 1,
  "profiles": {
    "google:default": {
      "type": "api_key",
      "provider": "google",
      "key": "AIzaSy..."
    }
  }
}
```

`openclaw.json`の`auth.profiles`はキーなしのシンプルな形にしておく：

```json
"auth": {
  "profiles": {
    "google:default": {
      "provider": "google",
      "mode": "api_key"
    }
  }
}
```

## 2. モデルの設定

```bash
docker exec <name>-openclaw openclaw config set agents.defaults.model google/gemini-2.5-flash
```

または`openclaw.json`に直接：

```json
"agents": {
  "defaults": {
    "model": {
      "primary": "google/gemini-2.5-flash",
      "fallbacks": ["google/gemini-2.5-pro"]
    }
  }
}
```

---

## 3. python3 + 画像生成（nanobanana）

**デフォルトのDockerイメージにはpython3が入っていない。**
nanobananaスキル（`generate.py`）を使うには`Dockerfile`にpython3を追加する必要がある。

```dockerfile
RUN apt-get update && apt-get install -y tzdata git wget python3 python3-pip python3-venv && \
    ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    echo "Asia/Tokyo" > /etc/timezone && \
    pip3 install --break-system-packages google-generativeai pillow requests && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
```

リビルドが必要：

```bash
docker build -t bonsoleil/openclaw:latest .
docker restart <name>-openclaw
```

---

## 4. macOS Monterey（Intel）でのDocker環境構築

2015 MBP (macOS 12 Monterey / Intel) での検証結果：

| 方法 | 結果 | 理由 |
| --- | --- | --- |
| Colima + qemu | ❌ 超遅い | ソースビルド多数、依存地獄 |
| OrbStack | ❌ 非対応 | macOS Sonoma (14) 以上必須 |
| Docker Desktop 4.15 | ✅ 動作！ | `https://desktop.docker.com/mac/main/amd64/93002/Docker.dmg` |

**ポイント：**
- Docker Desktop起動後に「アップデート」ダイアログが出るが、macOS 12では更新できないため実質4.15のまま固定
- `docker compose`は古いAPIバージョンとの互換性エラーが出ることがある → `docker run`で直接起動する
- `docker`コマンドがPATHに入っていない場合は`/usr/local/bin/docker`でフルパス指定

---

## 5. Telegram接続

ネイティブ環境で使っていたBot Tokenとallowlistをそのままコンテナに移植できる。

`openclaw.json`に追加：

```json
"channels": {
  "telegram": {
    "enabled": true,
    "dmPolicy": "allowlist",
    "botToken": "your-bot-token",
    "allowFrom": ["telegram-user-id-1", "telegram-user-id-2"],
    "groupPolicy": "allowlist"
  }
}
```

再起動後にTelegramから話しかければ接続完了。
