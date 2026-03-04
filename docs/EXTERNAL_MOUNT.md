# 外部マウント設定ガイド

コンテナ内のAIがホスト側のファイルにアクセスできるようにするためのマウント設定。

---

## 基本構造

```
openclaw-docker/
├── instances/
│   └── <name>/
│       └── .openclaw/          ← OpenClaw内部データ（セッション・設定等）
└── sample_workspace/
    └── <name>/                 ← SOUL.md等のワークスペースファイル
```

`docker-compose.yml` のマウント設定：

```yaml
volumes:
  # OpenClaw内部データ（セッション・設定・ログ等）
  - ./instances/<name>/.openclaw:/home/node/.openclaw

  # ワークスペース（SOUL.md / IDENTITY.md / MEMORY.md等）
  - ./sample_workspace/<name>:/home/node/.openclaw/workspace
```

---

## ワークスペースファイルの編集

ホスト側の `sample_workspace/<name>/` を直接編集すれば、
コンテナ再起動なしで次回セッション起動時に反映される。

```bash
# ホスト側で直接編集
vim sample_workspace/mephi/SOUL.md

# コンテナ再起動不要（次のTUI接続時に反映）
```

---

## MEMORY.md の場所

AIがMEMORY.mdを書いた場合、コンテナ内では：

```
/home/node/.openclaw/workspace/MEMORY.md
```

ホスト側では：

```
sample_workspace/<name>/MEMORY.md
```

コンテナ内で書かれたファイルはマウント経由でホスト側にも反映される。

> **注意:** `.openclaw/workspace/` をマウントしていない構成の場合、
> コンテナ内で書いたファイルはホスト側に残らない。
> 必ず `sample_workspace/<name>` をワークスペースとしてマウントすること。

---

## ホスト側のデータをAIに読ませたい場合

例：history.txtやPDFなど、外部データをコンテナ内に見せたい場合。

```yaml
volumes:
  - ./instances/<name>/.openclaw:/home/node/.openclaw
  - ./sample_workspace/<name>:/home/node/.openclaw/workspace
  # 追加マウント例
  - /Users/teddy/documents/project:/home/node/data:ro  # 読み取り専用
```

AI側からは `/home/node/data/` としてアクセスできる。

---

## セッションファイルへのアクセス

セッションJSONLはホスト側から直接編集可能：

```
instances/<name>/.openclaw/agents/main/sessions/
├── sessions.json               ← セッション一覧・メタデータ
└── <session-id>.jsonl          ← 会話履歴
```

記憶注入もここに対して行う。詳細は [MEMORY_INJECTION.md](./MEMORY_INJECTION.md) を参照。

---

## パーミッション注意事項

macOSでのUID/GID設定：

```bash
# .env に記載
CONTAINER_UID=501   # macOSデフォルトユーザー
CONTAINER_GID=20    # staffグループ
```

Linuxの場合は `1000:1000` が一般的。

マウントしたファイルがコンテナから書き込めない場合：

```bash
# ホスト側でパーミッション確認
ls -la instances/<name>/
# コンテナユーザーと一致させる
chown -R 501:20 instances/<name>/
```
