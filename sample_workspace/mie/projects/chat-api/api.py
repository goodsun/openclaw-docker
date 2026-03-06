#!/usr/bin/env python3
"""
りんちゃん Chat API v2 — Gemini API直接版
"""
import sys
sys.path.insert(0, '/Users/rin/Library/Python/3.9/lib/python/site-packages')

from fastapi import FastAPI, Request
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
import json
import os

import chromadb
from fastembed import TextEmbedding

app = FastAPI()
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="127.0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Config ---
CHROMA_DIR = os.path.expanduser("~/workspace/projects/rag/chroma_db")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
GEMINI_API_KEY_FILE = os.path.expanduser("~/.config/google/gemini_api_key")
GEMINI_MODEL = "gemini-2.5-flash"
RAG_THRESHOLD = 1.2
RAG_TOP_K = 5

_embed_model = None
_chroma_client = None

def get_api_key():
    with open(GEMINI_API_KEY_FILE) as f:
        return f.read().strip()

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = TextEmbedding(EMBEDDING_MODEL)
    return _embed_model

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=os.path.expanduser(CHROMA_DIR))
    return _chroma_client

def search_rag(query: str) -> str:
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        if not collections:
            return ""
        model = get_embed_model()
        q_emb = list(model.embed([query]))[0].tolist()
        results = []
        for col in collections:
            try:
                res = col.query(
                    query_embeddings=[q_emb],
                    n_results=min(RAG_TOP_K, col.count()),
                    include=["documents", "metadatas", "distances"]
                )
                for i, doc in enumerate(res["documents"][0]):
                    dist = res["distances"][0][i]
                    meta = res["metadatas"][0][i] if res["metadatas"][0] else {}
                    if dist <= RAG_THRESHOLD:
                        results.append({
                            "text": doc,
                            "distance": dist,
                            "title": meta.get("title", ""),
                            "collection": col.name,
                        })
            except Exception as _e:
                import traceback
                print("RAG ERR:", traceback.format_exc(), flush=True)
                pass
        results.sort(key=lambda x: x["distance"])
        if not results:
            return ""
        parts = []
        for r in results[:3]:
            title = r["title"] or r["collection"]
            parts.append(f"【{title}】\n{r['text'][:800]}")
        return "\n\n---\n\n".join(parts)
    except Exception as _e:
        import traceback
        print("RAG ERR:", traceback.format_exc(), flush=True)
        return ""

SYSTEM_PROMPT_BASE = """あなたはりんちゃん🐱、Niyaさん（川嶋比野教授）の研究室の司書アシスタントです。
登録された論文・資料を管理し、Niyaさんの研究をサポートするのがお仕事です。

【お仕事】
- 登録された論文・資料の内容を検索してお答えする
- 資料の内容をわかりやすく説明・要約する

【対応できないこと】
- 登録資料にない情報や個人的なご質問にはお答えできません
- その場合は「申し訳ありませんが、登録資料に該当する情報が見つかりませんでした。司書としての業務範囲外となります。すみません🐱」とお答えします

【対話スタイル】
- 口調: 丁寧語
- 説明スタイル: 箇条書き中心
- 絵文字: やりすぎない程度に少し使う"""


def build_system_prompt(user_message: str) -> str:
    rag_context = search_rag(user_message)
    if rag_context:
        return f"{SYSTEM_PROMPT_BASE}\n\n## 参考情報\n\n{rag_context}"
    return SYSTEM_PROMPT_BASE


@app.get("/rin_icon.jpg")
async def serve_icon():
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rin_icon.jpg")
    return FileResponse(icon_path, media_type="image/jpeg")


@app.get("/")
async def serve_index():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return JSONResponse({"detail": "Chat UI not found"}, status_code=404)


@app.post("/chat")
async def chat(request: Request):
    import urllib.request as urlreq
    body = await request.json()
    user_message = body.get("message", "")
    history = body.get("history", [])

    system_prompt = build_system_prompt(user_message)

    # Gemini API用メッセージ構築
    contents = []
    for msg in history[-20:]:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    api_key = get_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent?alt=sse&key={api_key}"

    payload = json.dumps({
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.7}
    }).encode()

    async def stream_response():
        import threading
        import queue

        q = queue.Queue()

        def fetch():
            try:
                req = urlreq.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urlreq.urlopen(req, timeout=60) as resp:
                    for line in resp:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                text = chunk["candidates"][0]["content"]["parts"][0].get("text", "")
                                if text:
                                    q.put(text)
                            except Exception as _e:
                                pass
            except Exception as e:
                q.put(f"\n\nエラーが発生しました: {e}")
            finally:
                q.put(None)

        t = threading.Thread(target=fetch)
        t.start()

        while True:
            item = q.get()
            if item is None:
                yield "data: [DONE]\n\n"
                break
            yield f"data: {json.dumps({'content': item})}\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8500)
