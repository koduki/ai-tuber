# AI Tuber ドキュメント

AI Tuber は、**魂（Saint Graph）**、**肉体（Body）**、**精神（Mind）** の三位一体で構成される AITuber システムです。

---

## クイックスタート

初めての方は [セットアップガイド](./knowledge/setup.md) から始めてください。

---

## アーキテクチャ

システム全体の設計:

- [システム概要](./architecture/overview.md) - 三位一体構造の説明
- [通信プロトコル](./architecture/communication.md) - REST/MCP 仕様
- [データフロー](./architecture/data-flow.md) - 処理シーケンス

---

## Components

### Saint Graph（魂）

意思決定エンジン:

- [概要](./components/saint-graph/README.md)
- [コアロジック](./components/saint-graph/core-logic.md) - Agent とターン処理
- [ニュース配信](./components/saint-graph/news-service.md) - ニュース管理
- [Body クライアント](./components/saint-graph/body-client.md) - REST クライアント
- [プロンプト設計](./components/saint-graph/prompts.md) - プロンプトシステム

### Body（肉体）

ストリーミング制御:

- [概要](./components/body/README.md)
- [アーキテクチャ](./components/body/architecture.md) *(作成予定)*
- **Streamer モード**:
  - [概要](./components/body/streamer/overview.md) *(作成予定)*
  - [OBS Studio](./components/body/streamer/obs-studio.md) *(作成予定)*
  - [VoiceVox](./components/body/streamer/voicevox.md) *(作成予定)*
  - [YouTube 統合](./components/body/streamer/youtube.md) *(作成予定)*
  - [音声生成・再生](./components/body/streamer/audio-playback.md) *(作成予定)*
- **CLI モード**:
  - [概要](./components/body/cli/overview.md) *(作成予定)*
- **外部ツール**:
  - [天気ツール](./components/body/tools/weather.md) *(作成予定)*

### Mind（精神）

キャラクター定義:

- [概要](./components/mind/README.md) *(作成予定)*
- [キャラクターシステム](./components/mind/character-system.md) *(作成予定)*
- [感情制御](./components/mind/emotion-control.md) *(作成予定)*
- [キャラクター作成ガイド](./components/mind/character-creation-guide.md) *(作成予定)*

---

## ガイド

利用方法と参考資料:

- [セットアップ](./knowledge/setup.md) - 環境構築と起動方法
- [YouTube 配信セットアップ](./knowledge/youtube-setup.md) - OAuth 認証と配信設定
- [開発者ガイド](./knowledge/development.md) - 開発環境とテスト実行
- [トラブルシューティング](./knowledge/troubleshooting.md) - よくある問題と解決方法

---

## ドキュメント構成

### `/architecture/` - アーキテクチャ設計
システム全体の設計と通信仕様

### `/components/` - コンポーネント仕様
各サービスの技術仕様を三位一体構造で整理:
- `saint-graph/` - 魂（意思決定）
- `body/` - 肉体（入出力制御）
- `mind/` - 精神（キャラクター定義）

### `/knowledge/` - ナレッジベース
セットアップ、開発、トラブルシューティング、過去の知見

---

## 貢献

新しいドキュメントを追加する場合は、三位一体構造に従って適切なディレクトリに配置してください。

---

**最終更新**: 2026-02-02
