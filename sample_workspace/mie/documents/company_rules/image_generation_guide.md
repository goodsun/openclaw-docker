# 画像生成ガイドライン — bon-soleil Holdings

実践から得られた知見をまとめたガイドライン。
generate.py（nanobanana skill）を使った画像生成の運用ルール。

## ref とプロンプトテキストの役割分担

### 大原則: テキストが ref より優先される

Gemini はプロンプトテキストを ref 画像より強く優先する。
**キャラクターの外見はテキスト（prompt_features）で書く。ref はニュアンスの補完。**

| 要素 | 役割 | 例 |
|------|------|-----|
| `prompt_features` | キャラの外見定義（最優先） | 髪色・服装・角・耳など |
| `charsheet`（ref） | タッチ・色味・雰囲気の補完 | ベージュ暖色系のマンガ調など |

### よくある失敗

- ref だけ変えて prompt_features を変えない → 同じキャラが出続ける
- ref を渡さず prompt_features だけ → 外見は正確だがタッチが安定しない
- **両方揃えるのがベスト**

## ref と prompt_features の競合回避

### 原則: ref の内容を壊す prompt_features を書かない

ref（charsheet）を指定した場合、その ref に描かれている要素と矛盾する記述を prompt_features に含めてはならない。

**prompt_features 記述ルール:**

1. **ref の内容を先に確認する** — 何を着ているか、髪型はどうか、ポーズは何か
2. **ref と重複・矛盾する外見描写を入れない** — ref に任せる部分は書かない
3. **prompt_features はシーン・状況・表情など、ref に含まれない要素を書く**

AI生成・手書きを問わず、prompt_features を記述する際はこのルールに従うこと。

### 具体例

| ref | prompt_features に書いてはいけない | 書くべきこと |
|-----|-------------------------------|------------|
| casual.png（カーディガン姿） | ~~sage green kimono~~, ~~着物~~ | カフェの雰囲気、表情、動作 |
| dressup.png（ドレス姿） | ~~casual wear~~, ~~パーカー~~ | パーティーの場面、ポーズ |
| 実物写真（備前焼の器） | ~~丸い茶碗~~, ~~角張った形~~ | 器の使われ方、食卓の雰囲気 |

## スタイル切替は必ず両方セットで

ref と prompt_features の矛盾を構造的に防ぐには、preset のスタイル定義で override をセットで定義する。

```json
"casual": {
  "charsheet_override": "~/workspace/HR/charsheets/akiko_bizeny/casual.png",
  "prompt_features_override": "young Japanese-French woman with dark brown hair in a relaxed low ponytail, beige knit cardigan over white blouse, taupe straight-leg pants, rosy cheeks"
}
```

**`charsheet_override` と `prompt_features_override` は必ずセットで定義する。**
片方だけでは切り替わらない。

**override を定義する場合、元の prompt_features から衣装の記述を差し替えること。**
元の prompt_features をコピーして衣装部分だけ書き換えるのが確実。

## モデル選定

モデル名は頻繁に変わるため、**選定原則**で判断する。付録の現行モデル表も参照。

### 選定原則

| 用途 | 求める特性 |
|------|-----------|
| 写真合成・テキスト描画 | ref反映精度が高い最高品質モデル |
| キャラ生成・高速処理 | フィルタが緩く、スタイル参照が得意なモデル |
| 3キャラ以上同時生成 | IPフィルタが緩いモデル（複数キャラでIP判定されやすい） |

### 付録: 現行モデル表（2026-02時点）

> ⚠️ モデル名は変更される可能性があります。最新情報は各プロバイダーのドキュメントを参照。

| モデル | 向いている用途 | 特記 |
|--------|-------------|------|
| `gemini-3-pro-image-preview` | 写真合成・テキスト描画・最高品質 | ref 反映精度◎、フィルタやや厳しい |
| `gemini-2.5-flash-image` | キャラ生成・スタイル参照・高速 | フィルタ緩め、テキスト描画は不得意 |

## 生成物の管理

```
workspace/assets/tmp/      ← 生成直後はここに出力（ステージング）
↓ 確認・採用
workspace/assets/images/   ← 公開用
workspace/HR/charsheets/   ← 社員のキャラシート
```

- **試行錯誤（v1, v2...）は assets/tmp/ に溜める**
- 採用後に正しい場所にコピー
- `assets/tmp/` は揮発データ（7日以上経過でクリーンアップ対象、.gitignore対象）
- SNS 投稿成功後も assets/tmp/ から削除

## 生成前の確認事項

- **生成前にマスターに確認を取ること**（自動生成が許可されているタスクを除く）
- 画像サイズ確認（100KB 超はリサイズしてから image ツールで確認）
- 生成後は即 Telegram でマスターに送る

---

*bon-soleil Holdings — 実践から学んだ画像生成ルール*
