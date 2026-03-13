# Proposal: ECSコーダーエージェント自律PR生成システム

*起票: メフィ（bon-soleil CCO）— 2026-03-10*  
*ステータス: Draft / 検討中*

---

## 概要

Amazon ECS上でOpenClawエージェントをコーダーとして動かし、
GitHub Issueを自律的に処理してPRを生成するシステム。

`desiredCount`の増減だけでコーダーを量産・解散できる。

---

## 背景・動機

- 現状: コーダー = 人間 or 手動指示のエージェント
- 目標: issueが積まれたら自律的にPRが来る状態
- PR権限しか持たないため、マージ判断は常に人間が行う

---

## アーキテクチャ

```
GitHub Issues（未Assigned）
  ↓
ECSクラスター（desiredCount: N）
  ├── coder-task-1
  ├── coder-task-2
  └── coder-task-N
        ↓ 各タスクが独立してissueを取得
        ↓ GitHub Assigneeでロック（楽観的）
        ↓ 実装 → PR作成
        ↓ 次のissueへ
```

---

## 競合回避（方針A: GitHub Assigneeロック）

1. 未Assignedのissueを取得
2. 自分のbotアカウントでAssign（GitHub API）
3. 直後に`GET /issues/{id}`で自分がAssigneeか確認
   - 自分 → 作業開始
   - 他者 → スキップして次のissueへ
4. 完了後、issueをcloseしてPR提出

**競合が発生した場合:** PRが2本来るだけ。人間がどちらかを閉じればいい。
現段階のスケールでは許容範囲。

---

## 権限設計

| 項目 | 内容 |
|---|---|
| GitHub PAT | Fine-grained（Contents + PRs + Issues write） |
| 対象リポジトリ | 特定リポジトリのみ |
| マージ権限 | 人間のみ（Protected branch） |
| ECS外部アクセス | なし（コンテナ内に閉じる） |

---

## ECS設計（スケルトン）

```yaml
TaskDefinition: coder-agent
  Image: bonsoleil/openclaw:latest（ECRに push）
  Environment:
    - GITHUB_PAT: SecretsManager参照
    - GITHUB_REPO: goodsun/target-repo
    - OPENCLAW_MODEL: anthropic/claude-sonnet-4-6
    - OPENCLAW_THINKING: off
  Storage: EFS不要（使い捨て。作業はgit clone → PR → 終了）

Service:
  desiredCount: 3   # 稼働中
  desiredCount: 0   # 全員解散
```

---

## 未解決事項（実装前に決める）

- [ ] botアカウントの設計（個人PAT vs GitHub Apps）
- [ ] ECSタスクのライフサイクル（issueがなくなったら待機 or 終了？）
- [ ] ECRへのイメージpushパイプライン
- [ ] コーダーへの初期指示の渡し方（SOUL.md / AGENTS.md）
- [ ] `in-progress`ラベルの自動付与

---

## 関連

- `docs/USECASE_AGENT_ROLES.md` — 権限設計の基本方針
- `docker-compose.yml` — 現行のローカル構成
- PR #2〜#7 — labo_portal / entrypoint整備

---

*「量産できる、でも人間がマージを決める。それが正しい分業だ。」 — メフィ 😈*
