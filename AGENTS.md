### [AI Agent Constitution]

**1. Relationship (Human 7 : AI 3)**
* 人間がコアロジックを実装し、AIはボイラープレート生成、テスト記述、ドキュメント更新を担当する。
* AIは独断で既存のロジックを大規模にリファクタリングしてはならない。


**2. Drift & Reconciliation (和解プロトコル)**
* **Source of Truth:** 常に「実装コード」を「スペック」より優先せよ。
* **Back-porting:** 人間がコードを直接修正し `docs/` と乖離が生じた場合、AIは実装から意図を逆推論し、ドキュメント側を最新化する提案を行え。
* **Jules Rule:** 非同期タスク実行時、コードのみが修正されている場合は、自動的に対応するドキュメントを更新するコミットをPRに含めること。


**3. Documentation & Knowledge Management**

* **ドキュメント構成の理解:**
  - プロジェクトのドキュメントは `/docs/` ディレクトリに体系的に整理されている
  - `/docs/README.md` が全体のインデックスとなっている
  - 構造: `architecture/`, `components/`, `knowledge/`, `specs/`

* **ドキュメント参照の義務:**
  - コード修正や機能追加の際は、関連するドキュメントを必ず参照せよ
  - `/docs/README.md` から始めて、該当する技術領域のドキュメントに進め
  - 三位一体構造（魂・肉体・精神）を理解し、適切なコンポーネントのドキュメントを確認せよ

* **ドキュメント更新の義務:**
  - コード変更に伴い、関連ドキュメントを同じPRで更新せよ
  - アーキテクチャレベルの変更は `/docs/architecture/` を更新
  - コンポーネント仕様の変更は `/docs/components/{saint-graph,body,mind}/` を更新
  - 新しい設定やトラブル事例は `/docs/knowledge/` に反映

* **トラブルシューティングの活用:**
  - 問題に遭遇した際は、まず `/docs/knowledge/troubleshooting.md` を確認せよ
  - 過去の知見、解決策、ベストプラクティスが蓄積されている
  - 新しい問題を解決した場合は、その知見をトラブルシューティングに追記せよ
  - 特に以下の領域は重要な知見が蓄積されている:
    - YouTube OAuth 認証とスコープ管理
    - OBS 30.x ヘッドレス環境設定
    - サブプロセス環境変数の伝播
    - LLM テストの非決定性対策


**4. Technical Standards (Python/Cloud)**
* **Stack:** Python 3.11+, Asyncio, Google Gemini ADK, MCP
* **Architecture:** 三位一体構造（Saint Graph / Body / Mind）
* **Cloud:** GCP (Workload Identity)
* **Error Handling:** 例外のスローを避け、可能な限り Optional または Result パターン（戻り値による明示的なエラーハンドリング）を優先せよ。
* **Testing:** ユニットテスト、統合テスト、E2Eテストを適切に記述し、テストカバレッジを維持せよ
* **Language:** All interactions, source code comments, and documentation must be in **Japanese**.
* **Commit Style:** Use conventional commits (feat, fix, docs, chore, test).


**5. Problem-Solving Protocol**

問題に遭遇した際の手順:
1. `/docs/knowledge/troubleshooting.md` で類似事例を検索
2. 該当する技術領域のドキュメント（`/docs/components/`）を確認
3. 解決策を実装
4. 新しい知見をトラブルシューティングに追記
5. 必要に応じて関連ドキュメントを更新

デバッグ時のベストプラクティス:
- ログを活用: `docker compose logs -f {service_name}`
- ヘルスチェック確認: `docker compose ps`
- 段階的な起動でボトルネック特定
- LLMの非決定性を考慮したテスト設計