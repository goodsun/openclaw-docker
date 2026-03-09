# エージェント役割設計 — ユースケース集

bon-soleil Holdings における、権限設計と役割分担のユースケース集。
「最小権限の原則」と「人間によるゲート」を基本方針とする。

---

## ケース1: Webデザイナーエージェント

### 概要

みぃちゃん（または専用インスタンス）にGitHub Pages等のサイトへの
**PRのみ**出す権限を与え、Webデザイナーとして自律的に働かせる構成。

### 権限設計

| 項目 | 設定 |
|---|---|
| GitHub PAT | Fine-grained PAT（スコープ限定） |
| PAT権限 | `Contents: Read` + `Pull requests: Write` |
| 対象リポジトリ | 特定リポジトリのみ（例: `goodsun/bon-soleil-web`） |
| mainブランチ | Protected branch（直pushを禁止） |
| マージ権限 | 人間（マスター）のみ |

### セットアップ

```bash
# 1. GitHub Fine-grained PATを発行
#    Settings > Developer settings > Personal access tokens > Fine-grained tokens
#    - Repository access: 対象リポジトリのみ
#    - Permissions: Contents(Read), Pull requests(Write)

# 2. .envに追加
echo "GITHUB_PAT=github_pat_XXXXXXXX" >> instances/mie/.env

# 3. ブランチ保護ルール設定
#    対象リポジトリ > Settings > Branches > Add rule
#    Branch name pattern: main
#    ✅ Require a pull request before merging
```

### ワークフロー

```
みぃちゃん
  ↓ デザイン変更を実装
  ↓ git commit & git push (feature branch)
  ↓ PR作成（タイトル・説明付き）
  ↓
マスター
  ↓ PRをレビュー
  ↓ マージ or 修正依頼
  ↓
GitHub Pages
  ↓ 自動デプロイ
```

### 安全性のポイント

- **PRを出せるだけでマージはできない** — 人間のレビューゲートが残る
- **Fine-grained PATでスコープ限定** — 万が一の漏洩時の被害を最小化
- **特定リポジトリのみ** — 他のリポジトリには触れない
- **コンテナ内に閉じた環境** — SSH等の外部アクセス手段なし

### 拡張パターン

```yaml
# docker-compose.yml（mieサービスに追加）
environment:
  - GITHUB_PAT=${GITHUB_PAT}
  - GITHUB_REPO=goodsun/bon-soleil-web
```

---

## 基本方針

### 最小権限の原則
エージェントには「今のタスクに必要な最小限の権限」だけを渡す。
後から追加することは簡単だが、削ることは難しい。

### 人間によるゲート
最終的な意思決定（マージ、デプロイ、公開）は人間が行う。
エージェントは「提案」と「実装」を担い、「承認」は人間の仕事。

### スコープの明示
何ができて何ができないかを`.env`と`docker-compose.yml`で
コードとして明示する。暗黙の権限は作らない。

---

*Reviewed by Mephi 😈 (bon-soleil CCO)*
