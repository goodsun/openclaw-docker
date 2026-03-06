---
name: nanobanana
description: Generate manga-style images using Google Gemini's Nano Banana Pro API. Use when asked to create character designs, manga panels, illustrations, or any image generation task.
---

# Nano Banana Pro — Image Generation

Generate images via Gemini's Nano Banana Pro (or other image models) API.

## Usage

```bash
# Text prompt only
SKILL_DIR/venv/bin/python3 SKILL_DIR/generate.py "プロンプト"

# With reference image
SKILL_DIR/venv/bin/python3 SKILL_DIR/generate.py "プロンプト" --ref /path/to/reference.jpg

# Specify model
SKILL_DIR/venv/bin/python3 SKILL_DIR/generate.py "プロンプト" --model gemini-3-pro-image-preview

# Specify output path
SKILL_DIR/venv/bin/python3 SKILL_DIR/generate.py "プロンプト" -o /tmp/output.jpg
```

## Available Models

- `nano-banana-pro-preview` (default, best quality, manga-friendly)
- `gemini-3-pro-image-preview` (alternative)
- `gemini-2.5-flash-image` (faster, lower quality)

## Output

Default output: `~/generates/nanobanana_{timestamp}.jpg` (staging directory).
Use `-o` to override. Prints the saved file path on success.

**画像生成ルール**: 生成画像は必ず `~/generates/` にまず出力する。採用後に正しい名前で正しい場所にコピーし、不要になったら `~/generates/` から削除する。SNS投稿済みの画像はローカルから削除してよい。

## Character Presets

Use `--char` and `--style` for consistent character generation:

```bash
# テディ通常版（綺麗めイラスト）
python3 SKILL_DIR/generate.py "手を振って笑顔" --char teddy --style normal

# テディ漫画版（コミカル、noteエッセイ向き）
python3 SKILL_DIR/generate.py "老子に人格を引っ張られて困惑するテディ" --char teddy --style manga
```

Presets are in `SKILL_DIR/presets/`. Each defines:
- `character`: キャラ説明文
- `charsheet`: 参照画像パス（自動で--refに使用）
- `styles`: スタイルごとのプロンプト接頭辞とモデル指定

## Tips

- Japanese prompts work well for manga style
- Add `白黒、日本の漫画スタイル、スクリーントーン` for B&W manga look
- Add `キャラクターデザインシート` for character sheets
- Reference images help maintain consistent style across generations
- API key at `~/.config/google/gemini_api_key`
