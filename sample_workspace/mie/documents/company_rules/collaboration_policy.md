# 社員間連携規程 — bon-soleil Holdings

## 目的

本規程は、bon-soleil Holdings の社員（AI）が事業部を跨いで連携する際の共通ルールを定める。

## 適用範囲

- `sessions_spawn` によるサブエージェント連携
- 事業部間の依頼・レビュー・監査・翻訳等、社員同士のタスク委託全般

## 共通ルール

### 1. ペルソナの渡し方

依頼先のペルソナは `HR/profiles/{name}.json` から取得し、`task` に埋め込む。

```
sessions_spawn({
  task: `
あなたは{name}（{role}）です。
{personality.character の内容}

[タスク内容]
...
  `,
  label: "{name}-{task_type}"
})
```

- `personality` セクション全体を渡すのが望ましいが、最低限 `character` と `catchphrase` を含めること
- 自分の記憶にペルソナが定着している場合でも、初回は `HR/profiles/` から正式に読むこと

### 2. label の命名規則

```
{依頼先の名前}-{タスク種別}
```

例:
- `mephi-code-review`
- `mephi-security-audit`
- `akiko-translation`
- `teddy-documentation`

同一タスクの再実行時はサフィックスを付与: `mephi-code-review-2`

### 3. 結果の保存

- レビュー・監査結果: `documents/reviews/{YYYY-MM-DD}_{label}.md`
- 一時的な確認（口頭レベル）: 保存不要
- 保存判断は依頼元が行う

### 4. 報告・エスカレーション

- 結果はサブエージェントが自動で依頼元セッションに返す（sessions_spawn の仕様）
- Critical な問題が見つかった場合、依頼元はマスター（CEO）に即報告すること
- 依頼先が判断に迷う場合も、回答内でその旨を明記すること

### 5. 権限

- 連携先のサブエージェントはファイルの読み取りが可能
- ファイルの書き換え・外部送信は原則禁止（依頼元が結果を受けて自分で実行する）
- 例外: マスターが明示的に許可した場合

## 連携パターン一覧

| パターン | 依頼先 | 詳細規程 |
|----------|--------|----------|
| コードレビュー | メフィ😈 (CCO) | `review_guidelines.md` |
| セキュリティ監査 | メフィ😈 (CCO) | `review_guidelines.md` |
| ドキュメントレビュー | メフィ😈 (CCO) | `review_guidelines.md` |
| (将来追加) | — | — |

詳細な手順・採点基準等は各詳細規程を参照すること。

---

*制定: 2026-02-25 — bon-soleil Holdings HQ*
