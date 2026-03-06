---
name: rag-ingest
description: NiyaさんがPDFや文書ファイルを送ってきたらRAGに取り込む。「RAGに入れて」「覚えて」「論文追加」などの指示や、PDFファイルの添付があったときに使う。
---

# RAG Ingest

NiyaさんからPDFや文書を受け取り、りんちゃんのRAGに取り込むスキル。

## 手順

1. ファイルを受け取ったら `/Users/rin/workspace/documents/papers/` に保存する
2. 以下のコマンドでRAGに取り込む:

```bash
# PDFをチャンク化
python3 /Users/rin/workspace/projects/rag/scripts/scrape_pdf.py \
  /Users/rin/workspace/documents/papers/ \
  /tmp/new_chunks.json

# chunk_idを追加
python3 -c "
import json
with open('/tmp/new_chunks.json') as f: chunks = json.load(f)
for c in chunks: c['chunk_id'] = c['id']
with open('/tmp/new_chunks.json', 'w') as f: json.dump(chunks, f)
print(len(chunks), 'chunks ready')
"

# Chromaに格納
cd /Users/rin/workspace/projects/rag && \
python3 scripts/embed.py --collection papers --chunks /tmp/new_chunks.json --append
```

3. 完了したらNiyaさんに「〇〇を△チャンクに分けてRAGに取り込みました！」と報告する

## 注意

- PDFは `/Users/rin/workspace/documents/papers/` に保存する
- 取り込み後、RAGAPIが自動で最新データを返す（再起動不要）
- 重複して取り込まないよう、すでに同名ファイルがある場合は確認する
