# ネイティブ環境 → Docker環境 移行注意事項

ネイティブのOpenClaw環境をDockerコンテナに移行する際の注意点まとめ。
りんちゃん（hino machine）の移行作業（2026-03-05）から得た知見。

---

## 1. パスの変換

ネイティブ環境ではホームディレクトリ（`~`）が `/Users/<username>` や `/home/<username>` だが、
コンテナ内では `/home/node` に固定される。

**AGENTS.md / TOOLS.md / スクリプト内のパスを一括置換する：**

```bash
# ワークスペースパスの置換
sed 's|~/workspace|/home/node/.openclaw/workspace|g' AGENTS.md > AGENTS.md.tmp && mv AGENTS.md.tmp AGENTS.md
```

### よくあるパス対応表

| ネイティブ | Docker内 |
| --- | --- |
| `~/workspace/` | `/home/node/.openclaw/workspace/` |
| `~/workspace/skills/nanobanana/generate.py` | `/home/node/.openclaw/workspace/skills/nanobanana/generate.py` |
| `~/workspace/assets/` | `/home/node/.openclaw/workspace/assets/` |
| `~/generates/` | ⚠️ コンテナ外 → ボリュームマウントが必要 |
| `~/.config/` | ⚠️ コンテナ外 → 別途対応 |

---

## 2. Gemini APIキーの設定

**`openclaw.json`の`auth.profiles`にAPIキーは書かない**（フォーマットエラーになる）。

正しい設定場所：

```
instances/<name>/.openclaw/agents/main/agent/auth-profiles.json
```

```json
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

ネイティブ環境から移植する場合：

```bash
cp ~/.openclaw/agents/main/agent/auth-profiles.json \
   instances/<name>/.openclaw/agents/main/agent/
```

---

## 3. Telegramの引き継ぎ

Bot TokenとallowlistをネイティブのopenclawjsonからDockerの`openclaw.json`に移植する。

ネイティブの設定確認：

```bash
cat ~/.openclaw/openclaw.json | python3 -m json.tool | grep -A10 '"telegram"'
```

`openclaw.json`に追加：

```json
"channels": {
  "telegram": {
    "enabled": true,
    "dmPolicy": "allowlist",
    "botToken": "your-bot-token",
    "allowFrom": ["user-id-1", "user-id-2"],
    "groupPolicy": "allowlist"
  }
}
```

---

## 4. memory/ ファイルの移植

ネイティブで蓄積されたmemoryファイルをコンテナのworkspaceにコピーする：

```bash
cp -r ~/.openclaw/agents/main/workspace/memory/ \
      instances/<name>/workspace/memory/
# または
cp ~/workspace/memory/* instances/<name>/workspace/memory/
```

---

## 5. python3 / 画像生成（nanobanana）

**デフォルトのDockerイメージにはpython3が入っていない。**

`Dockerfile`に追加が必要（詳細は[GEMINI_SETUP.md](./GEMINI_SETUP.md)参照）。

nanobananaの`generate.py`が使う環境変数：
- `GOOGLE_API_KEY` — Gemini APIキー（`.env`で渡す）

---

## 6. docker composeのAPIバージョン問題（macOS Monterey）

Docker Desktop 4.15（macOS 12向け古いバージョン）では`docker compose`がAPIバージョンエラーを出すことがある。

```
unable to get image: client version 1.53 is too new. Maximum supported API version is 1.41
```

回避策：`docker compose`の代わりに`docker run`で直接起動する（[GEMINI_SETUP.md](./GEMINI_SETUP.md)参照）。

---

## 7. チェックリスト

移行完了の確認項目：

- [ ] `auth-profiles.json`がコンテナ内に存在する
- [ ] `openclaw.json`のモデルが正しく設定されている（`google/gemini-2.5-flash`等）
- [ ] AGENTS.mdのパスが`/home/node/.openclaw/workspace/`ベースに修正されている
- [ ] Telegram Bot Tokenが`openclaw.json`に設定されている
- [ ] `memory/`の重要ファイルがコピーされている
- [ ] `python3`が必要な場合はDockerfileに追加してリビルド済み
- [ ] TUIまたはTelegramで動作確認済み
