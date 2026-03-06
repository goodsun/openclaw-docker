# 📚 論文をRAGに取り込む手順書

**対象:** りんちゃん（BiblioChat RAG管理）  
**場所:** `~/workspace/projects/rag/`

---

## 手順

### 1. PDFを所定のフォルダに置く

```
~/workspace/documents/papers/ファイル名.pdf
```

staff portalのDocumentsページからアップロードしてもOK。

---

### 2. RAGに取り込む

以下のコマンドを実行：

```bash
/usr/bin/python3 ~/workspace/projects/rag/scripts/add_pdf.py \
  ~/workspace/documents/papers/ファイル名.pdf \
  --title "論文タイトル（日本語でも可）"
```

---

### 3. 確認

ragMyAdmin（http://192.168.1.21/ragmyadmin/）で `papers` コレクションを確認。  
ドキュメント数とチャンク数が増えていればOK！

---

## ⚠️ 注意

- 同じファイルを再取り込みすると古いチャンクを自動削除して上書きします（安全）
- チャンクサイズは800単語、オーバーラップ100単語
- 日本語PDFの場合、文字化けすることがあります（要確認）

---

## ファイルが増えたら一括取り込み

```bash
/usr/bin/python3 ~/workspace/projects/rag/scripts/add_pdf.py \
  ~/workspace/documents/papers/ --all
```

---

*作成: 2026-03-02 by テディ*
