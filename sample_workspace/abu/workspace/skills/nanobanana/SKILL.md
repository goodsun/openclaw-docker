---
name: nanobanana
description: Generate manga-style images using Google Gemini's Nano Banana Pro API. Use when asked to create character designs, manga panels, illustrations, or any image generation task.
---

# 画像生成スキル — labo-portal API

画像生成は `http://localhost:8800${APP_BASE}/image_gen/api/generate` を使う。
`APP_BASE` は環境変数から取得（例: `/abu`）。

詳細仕様は TOOLS.md の「labo-portal 画像生成 API」セクションを参照。

## 基本の流れ

1. APIキーとAPP_BASEを環境変数から取得する
2. プロンプト・キャスト・モデル・アスペクト比を決める
3. リクエストを送る（**直列で、1枚ずつ**）
4. 生成物を確認し、採用なら適切な場所に移動

## APIキー・ベースURL取得

```bash
API_KEY=${LABO_API_KEY}
BASE_URL="http://localhost:${LABO_PORT:-8800}${APP_BASE}"
```

## labo_portal起動確認・起動方法

```bash
# 起動確認
curl -s -o /dev/null -w "%{http_code}" http://localhost:${LABO_PORT:-8800}${APP_BASE}/

# 起動（止まってたら）
cd ~/workspace/projects/labo_portal && node dist/app.js > /tmp/labo.log 2>&1 &
sleep 3 && tail -5 /tmp/labo.log
```

## リクエスト例

```bash
# キャスト指定あり（彰子・normalスタイル）
curl -s -X POST ${BASE_URL}/image_gen/api/generate \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "warm anime style. 備前の工房で微笑む彰子",
    "cast_refs": "[{\"id\":\"akiko\",\"style\":\"normal\",\"label\":\"A\"}]",
    "gen_model": "gemini-3-pro-image-preview",
    "gen_aspect": "1:1"
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('filename'), d.get('ok'))"

# キャストなし（風景・物など）
curl -s -X POST ${BASE_URL}/image_gen/api/generate \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "備前焼の壺、窯の前、夕暮れ、warm anime style",
    "gen_model": "gemini-2.0-flash-exp-image-generation",
    "gen_aspect": "4:3"
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('filename'), d.get('ok'))"
```

## 画像ダウンロード（ログイン必要）

```python
import urllib.request, urllib.parse, http.cookiejar

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
import os
base_url = f"http://localhost:{os.environ.get('LABO_PORT','8800')}{os.environ.get('APP_BASE','')}"
opener.open(f"{base_url}/login", urllib.parse.urlencode({'password': os.environ.get('LABO_PASSWORD','')}).encode())

with opener.open(f"{base_url}/image_gen/img/{{filename}}") as r:
    data = r.read()
    with open('/home/node/workspace/data/assets/generated/output.png', 'wb') as f:
        f.write(data)
```

## キャスト一覧（cast_refs の id）

| id | キャラ |
|---|---|
| `akiko` | 彰子（Bizeny Akiko） |
| `mephi` | メフィ |
| `teddy` | テディ |
| `alice` | アリス |
| `jasmine` | ジャスミン |
| `goodsun` | マスター |
| `hino` | ひのちゃん（Niya） |
| `master` | マスター（別スタイル） |
| `abu` | アブ |
| `rin` | リン |

## akiko スタイル一覧

| style | 説明 |
|---|---|
| `normal` | 着物（デフォルト） |
| `pure` | 緑の雲紋着物・清楚な笑顔 |
| `misterius` | 紺の花柄着物・ミステリアス |
| `casual` | カーディガン姿 |
| `corporate` | スーツ姿 |
| `dressup` | エメラルドグリーンドレス |
| `armored` | 備前焼テクスチャの和風鎧 |
| `punk` | パリジェンヌ・パンクストリート |
| `racing` | レーシング |

## hino スタイル一覧

| style | 説明 |
|---|---|
| `normal` | 通常版（niya.jpg） |
| `pony` | ポニーテール版 |

## モデル選択

| gen_model | 特徴 |
|---|---|
| `gemini-3-pro-image-preview` | 高品質・ref対応（**テキスト描画・重要シーンはこれ**） |
| `gemini-2.0-flash-exp-image-generation` | 高速・ref対応 |
| `imagen-4.0-fast-generate-001` | 最速・refなし（キャスト指定不可） |

## アスペクト比

`1:1` / `3:4` / `4:3` / `9:16` / `16:9`

## タッチ指定（prompt に含める）

| タッチ | プロンプト例 |
|---|---|
| アニメ調 | `vibrant anime style, clean cel shading, bright colors` |
| 漫画調（温かみ） | `warm beige-toned soft manga style` |
| 漫画調（クール） | `cool-toned clean manga style, crisp linework` |
| セミリアル | `semi-realistic digital art, painterly finish` |
| スケッチ | `pencil sketch style, loose expressive linework, monochrome` |

## 重要ルール

- **生成は必ず直列（1枚ずつ）** — 並列実行禁止（サーバーがメモリ2GB）
- 生成物の保存先: `~/workspace/data/assets/generated/`
- 採用作品は手動で適切な場所にコピー（`~/workspace/assets/images/` など）
- 窯・登り窯シーンは背景refもセットで渡す（AIだと構造がおかしくなる）
- 背景素材: MEMORY.md「背景素材ライブラリ」参照
- Instagram投稿用は **1:1 か 4:5** にリサイズしてから投稿
