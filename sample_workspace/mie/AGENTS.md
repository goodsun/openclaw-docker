# AGENTS.md — 事業部運用ルール

## 初回起動
1. `config/division.json` の `name` を確認 — `"branch_office"` のままなら未セットアップ
2. 未セットアップなら `BOOTSTRAP.md` を読んで対話式にセットアップを進める
3. セットアップ済みなら `SOUL.md` → `USER.md` → `MEMORY.md` を読んで通常起動

## ディレクトリ規約

### ワークフロー: draft → review → adopt
- 生成物は `assets/tmp/` に仮置き → 採用分だけ `assets/images/` 等に移動
- 文書は `documents/drafts/` で起案 → 採択後 `documents/discussions/` 等に移動
- `tmp/` `drafts/` は定期クリーンアップ対象

### HR（人事）
- `HR/profiles/` — キャラプリセットJSON（この事業部の「社員」）
- `HR/charsheets/` — キャラ公式設定画
- 新キャラ追加 = 採用

### assets（作品素材）
- `assets/charsheets/` — 作品に登場するキャラ（IP）
- `assets/images/` — 公開用画像

## セキュリティ
- クレデンシャルは `config/` に置くか、PostgreSQLの shared.secrets を使う
- ファイルに平文でAPIキーを書かない
- 外部発信は SOUL.md で定義された範囲のみ

## 共有リソース
- RAG: PostgreSQL `shared.knowledge` スキーマ
- 機密情報: PostgreSQL `shared.secrets` スキーマ
- 事業部固有データ: PostgreSQL `{division}.*` スキーマ

## 😈 メフィ召喚ルール

メフィをサブエージェントとして召喚する際は以下を必ず実施：

1. **GitHub PATを渡す** — `~/.config/github/mephi_pat`（pull_requests: write, issues: write）
2. **PRレビュー・Issueコメントに記録を残す** — Telegramだけでなくgithub.comにも残す
3. **PATが不明な場合はテディに確認** — テディが`~/.config/github/mephi_pat`を管理している

```
# メフィ召喚タスクへのPAT渡し方
MEPHI_PAT=$(cat ~/.config/github/mephi_pat)
# → task文字列にPATを含めてsessions_spawnに渡す
```

## Git Rules
- **PRマージ後はブランチを即削除**: `git push origin --delete <branch>` でリモートブランチを削除し、`git pull` でローカルを更新する
- マージ済みブランチが残っていたら気づいたときに掃除する

## 🎨 画像生成（nanobanana）

 を使う。OpenClawのGatewayは不要。直接Gemini APIを叩く。



- APIキー: 
- モデル: （画像生成向き）
- プリセット: 
- 出力先: 

プリセットを使う場合:


## 🎨 画像生成（nanobanana）

`~/workspace/skills/nanobanana/generate.py` を使う。OpenClawのGatewayは不要。直接Gemini APIを叩く。

APIキー: `~/.config/google/gemini_api_key`
モデル: `gemini-2.5-flash-image`（画像生成向き）
プリセット: `~/workspace/skills/nanobanana/presets/rin.json`
出力先: `~/workspace/assets/tmp/`

使い方例:
  python3 ~/workspace/skills/nanobanana/generate.py "プロンプト" --model gemini-2.5-flash-image -o ~/workspace/assets/tmp/output.jpg

プリセットを使う場合（--charオプション）:
  python3 ~/workspace/skills/nanobanana/generate.py --char rin "プロンプト" -o ~/workspace/assets/tmp/output.jpg

## Python実行環境
- python3コマンドは必ず  を使うこと
-  だとパスが違うモジュールが見つからないエラーになる

## サブエージェント画像生成ルール
- サブエージェントが画像生成タスクを完了した際は、必ず生成された画像を依頼元のTelegramチャットIDへ送信すること。
- 送信ツールは `message` を使用し、`target` パラメータに依頼元のチャットIDを明示的に指定すること。

## 📚 PDFをRAGに取り込む

**必ずadd_pdf.pyを使うこと**（scrape_pdf.pyは使わない）

```bash
# 1本追加
/usr/bin/python3 ~/workspace/projects/rag/scripts/add_pdf.py   ~/workspace/documents/papers/ファイル名.pdf   --title 論文タイトル

# フォルダ内全部まとめて
/usr/bin/python3 ~/workspace/projects/rag/scripts/add_pdf.py   ~/workspace/documents/papers/ --all
```

詳細手順: ~/workspace/documents/manual/rag_import_howto.md
## 📝 MD/HTML/TXTをRAGに取り込む

```bash
# 1ファイル追加
/usr/bin/python3 ~/workspace/projects/rag/scripts/add_doc.py   ~/workspace/documents/manual/howto.md   --title タイトル

# フォルダ内全部まとめて
/usr/bin/python3 ~/workspace/projects/rag/scripts/add_doc.py   ~/workspace/documents/manual/ --all
```

対応形式: .md .txt .html .htm
