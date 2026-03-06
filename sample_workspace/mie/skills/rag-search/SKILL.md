---
name: rag-search
description: Search Niyaさん(川嶋比野)の論文やドキュメントをRAGで検索する。論文の内容、研究テーマ、過去の著作について質問されたときに使う。siegengin、XPathGenie、Monolith、備前焼、食器、盛り付けについて聞かれたときも使う。
---

# RAG Search

りんちゃんのRAGシステム。論文・ドキュメントをベクトル検索します。

## API

```bash
curl -s http://127.0.0.1:8501/search \
  -X POST -H "Content-Type: application/json" \
  -d '{"query": "検索クエリ", "n_results": 5}'
```

### Parameters
- `query` (string): 検索クエリ（日本語OK）
- `n_results` (int): 件数（デフォルト5）
- `collection` (string): コレクション名（省略時は全件）

### Response
```json
{
  "results": [
    {
      "text": "...",
      "distance": 0.42,
      "title": "論文タイトル",
      "collection": "papers"
    }
  ]
}
```

## Usage

- 検索結果を元に、質問に答える。
- 検索結果はJSON形式で表示せず、内容を要約して分かりやすく説明する。
- 回答は箇条書きで記述する。
- distanceが低いほど関連度が高いことを考慮する（0.6以下が目安）。
- 関連情報が見つからない場合は「資料にはありません」と伝える。
