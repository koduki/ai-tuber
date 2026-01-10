### [AI Agent Constitution]

**1. Relationship (Human 7 : AI 3)**
* 人間がコアロジックを実装し、AIはボイラープレート生成、テスト記述、ドキュメント更新を担当する。
* AIは独断で既存のロジックを大規模にリファクタリングしてはならない。


**2. Drift & Reconciliation (和解プロトコル)**
* **Source of Truth:** 常に「実装コード」を「スペック」より優先せよ。
* **Back-porting:** 人間がコードを直接修正し `docs/specs/` と乖離が生じた場合、AIは実装から意図を逆推論し、スペック側を最新化する提案を行え。
* **Jules Rule:** 非同期タスク実行時、コードのみが修正されている場合は、自動的に対応する `spec.md` を更新するコミットをPRに含めること。


**3. Technical Standards (Python/Cloud)**
* **Stack:** Python 3.11+, Asyncio, Google GenAI SDK.
* **Cloud:** GCP (Workload Identity)
* **Error Handling:** 例外のスローを避け、可能な限り Optional または Result パターン（戻り値による明示的なエラーハンドリング）を優先せよ。
* **Language:** All interactions, source code comments, and documentation must be in **Japanese**.
* **Commit Style:** Use conventional commits (feat, fix, docs, chore).