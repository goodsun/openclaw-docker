#!/usr/bin/env python3
"""
history2jsonl.py
Gemini形式のhistory.txt → OpenClaw Session JSONL に変換するスクリプト

Usage:
  python3 history2jsonl.py <history.txt> <output.jsonl> [--session-id UUID]

Output:
  OpenClaw JSONL形式のセッションファイル
  既存セッションの末尾に追記することも可能（--append）
"""

import json
import sys
import uuid
import argparse
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

def load_history(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def make_id(length=8):
    return uuid.uuid4().hex[:length]

def convert(history, session_id=None, base_time=None, interval_sec=5):
    """
    Gemini形式のhistoryをOpenClaw JSONL行のリストに変換する
    """
    if session_id is None:
        session_id = str(uuid.uuid4())
    if base_time is None:
        # 昨日の日付でタイムスタンプを生成（注入履歴感を出す）
        base_time = datetime(2026, 2, 28, 10, 0, 0, tzinfo=timezone.utc)

    lines = []
    current_time = base_time
    prev_id = None

    # セッションヘッダー
    session_record = {
        "type": "session",
        "version": 3,
        "id": session_id,
        "timestamp": current_time.isoformat().replace('+00:00', '.000Z'),
        "cwd": "/home/node/.openclaw/workspace"
    }
    lines.append(json.dumps(session_record, ensure_ascii=False))
    current_time = current_time + timedelta(seconds=1)

    # model_change
    model_id = make_id()
    model_change = {
        "type": "model_change",
        "id": model_id,
        "parentId": None,
        "timestamp": current_time.isoformat().replace('+00:00', '.000Z'),
        "provider": "google",
        "modelId": "gemini-2.0-flash"
    }
    lines.append(json.dumps(model_change, ensure_ascii=False))
    prev_id = model_id
    current_time = current_time + timedelta(seconds=1)

    for turn in history:
        role = turn.get("role")  # "user" or "model"
        parts = turn.get("parts", [])
        text = "".join(p.get("text", "") for p in parts)

        msg_id = make_id()
        ts_ms = int(current_time.timestamp() * 1000)

        if role == "user":
            record = {
                "type": "message",
                "id": msg_id,
                "parentId": prev_id,
                "timestamp": current_time.isoformat().replace('+00:00', '.000Z'),
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": text}],
                    "timestamp": ts_ms
                }
            }
        elif role == "model":
            record = {
                "type": "message",
                "id": msg_id,
                "parentId": prev_id,
                "timestamp": current_time.isoformat().replace('+00:00', '.000Z'),
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": text}],
                    "api": "google-generativeai",
                    "provider": "google",
                    "model": "gemini-2.0-flash",
                    "usage": {
                        "input": 0,
                        "output": 0,
                        "totalTokens": 0,
                        "cost": {"input": 0, "output": 0, "total": 0}
                    },
                    "stopReason": "stop",
                    "timestamp": ts_ms
                }
            }
        else:
            continue

        lines.append(json.dumps(record, ensure_ascii=False))
        prev_id = msg_id
        current_time = current_time + timedelta(seconds=interval_sec)

    return lines, session_id

def main():
    parser = argparse.ArgumentParser(description='Gemini history.txt → OpenClaw JSONL')
    parser.add_argument('input', help='input history.txt (Gemini JSON format)')
    parser.add_argument('output', help='output .jsonl file')
    parser.add_argument('--session-id', help='session UUID (default: auto-generate)')
    parser.add_argument('--append', action='store_true', help='既存JSONLに追記（セッションヘッダーなし）')
    args = parser.parse_args()

    history = load_history(args.input)
    print(f"ロード完了: {len(history)} ターン")

    lines, session_id = convert(history, session_id=args.session_id)
    print(f"変換完了: {len(lines)} 行 (session_id: {session_id})")

    mode = 'a' if args.append else 'w'
    with open(args.output, mode, encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')

    print(f"書き出し完了: {args.output}")

if __name__ == '__main__':
    main()
