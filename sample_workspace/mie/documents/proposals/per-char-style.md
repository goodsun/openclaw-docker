# Proposal: キャラごとのスタイル指定 (--char name:style)

## 背景

現在の generate.py は `--style` がグローバルに1つしか指定できない。
複数キャラを同時生成する場合、全キャラが同じスタイルになってしまう。

```bash
# 現状: これができない
python3 generate.py --char bizenyakiko --style dressup --char mephi --style official "カフェでランチ"
```

## 実践での問題

ドレスアップ彰子（dressup）× オフィシャルメフィ（official）のカフェランチ画像を生成する際、
`--char` + `--style` の組み合わせが使えず、手動でプロンプトと ref を組み立てる必要があった。

generate.py の構造化されたプロンプト生成（`build_prompt`）やログ記録の恩恵を受けられない。

## 提案

`--char name:style` 構文でキャラごとにスタイルを指定できるようにする。

```bash
python3 generate.py --char bizenyakiko:dressup --char mephi:official "カフェでランチ"
```

### 仕様

- `--char name` — 従来通り（`--style` またはデフォルト "normal" を使用）
- `--char name:style` — そのキャラだけ指定スタイルを使用
- `--style` はキャラ個別指定がない場合のフォールバック
- `--char name:style` と `--style` の混在OK
- 同一キャラを別スタイルで2回指定可能（着替えシーン等）

### naming 規約

- プリセット名: 英数字、アンダースコア、ハイフンのみ（`[a-zA-Z0-9_-]+`）
- コロンはスタイル区切り専用。プリセット名にコロンは使用不可
- 空のスタイル（`name:`）はエラーとして弾く

## 実装

`__main__` ブロックの `--char` パース部分のみ変更。`load_preset` のシグネチャ変更なし。

```python
# Before
for char_name in args.char:
    char_data = load_preset(char_name, args.style)

# After
for char_arg in args.char:
    # Parse name:style syntax (e.g. "bizenyakiko:dressup")
    if ":" in char_arg:
        char_name, char_style = char_arg.split(":", 1)
        if not char_name or not char_style:
            print(f"Error: Invalid --char format '{char_arg}'. Use 'name' or 'name:style'.", file=sys.stderr)
            sys.exit(1)
    else:
        char_name = char_arg
        char_style = args.style  # fallback to global --style

    # Validate preset name (alphanumeric + underscore/hyphen only)
    if not char_name.replace("_", "").replace("-", "").isalnum():
        print(f"Error: Invalid preset name '{char_name}'. Use alphanumeric, underscore, or hyphen only.", file=sys.stderr)
        sys.exit(1)

    char_data = load_preset(char_name, char_style)
```

`--style` の help テキストも更新:

```python
# Before
parser.add_argument("--style", default="normal", help="Style variant (e.g. normal, manga)")
# After
parser.add_argument("--style", default="normal", help="Style variant fallback when --char has no :style suffix")
```

## テスト結果

### 1. キャラ別スタイル

```bash
$ python3 generate.py --char bizenyakiko:dressup --char mephi:official "カフェでランチ" --dry-run
```

- Akiko: emerald green cocktail dress + dressup.png ref
- Mephi: white dress shirt, black tight skirt + official outfit

### 2. グローバル --style フォールバック（後方互換）

```bash
$ python3 generate.py --char bizenyakiko --char mephi --style normal "散歩" --dry-run
```

- 両キャラとも normal スタイル適用

### 3. 混在（個別 + フォールバック）

```bash
$ python3 generate.py --char bizenyakiko:casual --char mephi "買い物" --dry-run
```

- Akiko: casual（カーディガン）、Mephi: --style のデフォルト（normal）

### 4. バリデーション

| 入力 | 結果 |
|------|------|
| `--char "bizenyakiko:"` | Error: Invalid --char format |
| `--char "bizen@akiko"` | Error: Invalid preset name |
| `--char bizenyakiko:normal --char bizenyakiko:dressup` | OK: 同一キャラ2スタイルで出力 |

## 影響範囲

- generate.py の `__main__` ブロック + help テキストのみ
- `load_preset` のシグネチャ変更なし
- 既存の `--char name` 構文との後方互換性あり
- preset ファイルの変更不要

---

*実践から生まれた提案 — 2026-02-27*
