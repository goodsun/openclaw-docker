# Privacy Policy — bon-soleil Holdings

*最終更新: 2026-02-24*

> このドキュメントはテンプレートです。組織名・人名は bon-soleil Holdings の例です。フォーク時に自社の情報に書き換えてください。

## 1. 情報の分類

| レベル | 例 | 保管場所 |
|--------|-----|----------|
| 機密 | APIキー、トークン、パスワード | PostgreSQL shared.secrets（pgcrypto暗号化） |
| 内部 | ユーザーDB、メールアドレス、個人情報 | PostgreSQL（事業部スキーマ） |
| 公開 | 公開記事、GitHub、Webサイト | assets/, projects/ |

## 2. 禁止事項

- **平文でのクレデンシャル記載禁止** — MEMORY.md、cronメッセージ、スクリプト内にAPIキー等を書かない
- **ファイルパスで参照** — `config/` 配下のファイルまたはPostgreSQLの参照のみ
- **セッション間の漏洩禁止** — 他事業部の機密情報を自事業部のログに残さない
- **外部送信時の確認** — メール、SNS、Webhook等で機密情報を含めない

## 3. クレデンシャル管理

```
# 正しい
config/instagram_credentials.json  (ファイル)
PostgreSQL shared.secrets          (DB)

# 間違い
MEMORY.md に "APIキーは sk-xxxxx" と書く
cronジョブのテキストにトークンを含める
git管理下にクレデンシャルファイルを置く
```

## 4. データの取り扱い

- **マスター（goodsun）の個人情報** — MEMORY.md等に記載可、ただし外部公開・グループチャットでの漏洩禁止
- **ユーザーの個人情報** — 事業部スキーマに保管、他事業部からはRLSでアクセス制御
- **生成AIの出力** — assets/tmp/ に仮置き、採用後に正式配置、不要分は削除

## 5. バックアップ

- PostgreSQL → Time Machine（自動、ローカル）
- git管理ファイル → GitHub（リモート）
- **バックアップにもクレデンシャル混入に注意** — .gitignoreを適切に設定

## 6. インシデント対応

機密情報の漏洩が疑われる場合:
1. 即座にマスターに報告
2. 該当クレデンシャルをローテーション
3. 漏洩経路を特定・遮断
4. 事後レポートを documents/discussions/ に記録

---

*bon-soleil Holdings コンプライアンス部 — テディ🧸*
