---
name: github-pr-review
description: GitHub の PR 指摘（レビューコメント）をチェックし、修正案の実装、テスト、およびプッシュまでを一貫して行うためのスキル。
---

# GitHub PR Review Skill

このスキルは、GitHubの Pull Request (PR) における人間からのレビュー指摘や CI の失敗を、AI が自律的に解析・修正・反映するためのガイドラインと手順を提供します。
特に、このプロジェクトを理解するために、README.md, docs/, srcなどを理解し、設計思想と世の中のベストプラクティスに従い、適切に修正を行うことを目的とします。

## 1. 概要

GitHub CLI (`gh` コマンド) を活用し、PR の現在の状態、レビューコメント、およびチェック（CI）の実行結果を取得します。それらに基づいてコードを修正し、`git` を使用して変更をプッシュします。

- **使用ツール**: GitHub CLI (`gh`), Git
- **前提条件**: `gh` コマンドがインストールされ、リポジトリに対して認証済みであること。

## 2. 標準ワークフロー

PR の指摘に対応する際は、以下のステップを順に実行してください。

### Step 1: PR 状況の確認
現在のブランチに関連付けられた PR のステータスと、指摘事項（レビュー・コメント）を収集します。

```bash
# PR の全体像とコメント、レビュー状況を JSON 形式で取得
gh pr view --json number,title,body,reviews,comments,statusCheckRollup
```

### Step 2: 指摘事項の解析
取得した JSON から以下の情報を抽出します。
- **レビュー指摘 (`reviews`)**: `state: CHANGES_REQUESTED` や `state: COMMENTED` の各レビュー内にあるコメント。
- **インラインコメント (`comments`)**: 特定のファイル・行に対する指摘。
- **CI 失敗 (`statusCheckRollup`)**: 失敗しているチェックの名前と詳細。

### Step 3: コードの修正
各指摘事項に対し、以下の順序で対応します。

1.  **対象箇所とコンポーネントの特定**:
    - 指摘されたファイルが `Saint Graph`, `Body`, `Mind`, `dashboard`, `opentofu` のいずれに属するか特定します。
    - 関連するドキュメント（`/docs/components/{saint-graph,body,mind}/`）やREADME.mdを参照し、設計意図を再確認します。
    - `view_file` で現状のコードを確認します。

2.  **修正の実装**:
    - レビューの意図を汲み取り、最小限かつ確実な修正を行います。
    - **憲法遵守**: 大規模なリファクタリングは避け、指摘された箇所の改善に徹してください（Human 7 : AI 3）。
    - **エラーハンドリング**: 可能な限り Result/Optional パターンで行い、例外のスローを避けます。

3.  **ドキュメントの同期更新**:
    - コードの変更に伴い、関連するドキュメント (`/docs/`) も最新化します。
    - 特に `docs/knowledge/troubleshooting.md` に新しい解決策があれば追記します。

### Step 4: 検証
修正が正しいことを確認します。
- `npm test` や `pytest` 等、プロジェクト標準のテストスイートを実行します。
- `npm run lint` 等でスタイル違反がないか確認します。

### Step 5: コミットとプッシュ
修正をコミットし、リモートブランチへプッシュします。

```bash
# Conventional Commits に従ったメッセージ
git add .
git commit -m "fix: address pr review comments"
git push origin HEAD
```

## 3. GitHub CLI 活用テクニック

- **特定 PR の詳細取得**: `gh pr view <PR_NUMBER> --json ...`
- **チェックの失敗詳細**: `gh pr checks`
- **差分の確認**: `gh pr diff`
- **コメントの一覧**: `gh pr view --json comments --jq '.comments[].body'`

## 4. 指針と注意点

-   **Human 7 : AI 3**: AI はあくまで「指摘への対応」と「ボイラープレートの修正」を担当します。設計の根本に関わる変更が必要と判断した場合は、独断で進めず人間に相談してください。
-   **コミットメッセージ**: `fix:`, `docs:`, `chore:`, `test:` などのプレフィックスを適切に使用してください。
-   **同一ファイルへの複数修正**: 複数の指摘が同じファイルにある場合は、`multi_replace_file_content` を使用して一括で修正することを検討してください。
-   **完了報告**: どの指摘に対してどのような対応（修正・ドキュメント更新）を行ったか、最後に明示的に報告してください。

## 5. 困ったときは

- 過去の類似の修正事例や、特定のコマンドエラー（`gh` の権限不足等）については、`/docs/knowledge/troubleshooting.md` を参照してください。
- 解決した新しい知見は、同ドキュメントに追記してください。