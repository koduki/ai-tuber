# CLI コンポーネント (CLI モード)

**CLI** コンポーネントは、開発、テスト、およびデバッグを目的とした AI Tuber の「肉体（Body）」の軽量実装です。複雑な OBS や Voicevox 連携を必要とせず、標準入出力 (CLI) で動作します。

## 概要

CLI モードは、システムの「脳（Mind）」のロジックを検証したり、外部ツールとの連携をデバッグしたりする際に非常に有用です。[`BodyServiceBase`](../../../src/body/service.py) インターフェースに準拠しており、Mind 側からは Streamer モードと透過的に切り替えて使用できます。

## 機能

- **テキスト発話**: AI の応答を標準出力に表示します。
- **感情変更**: 感情の切り替えをコンソールにログ出力します。
- **コメント入力**: 標準入力からユーザーコメントをシミュレートできます。
- **配信制御**: 配信の開始・停止は No-op（何もしない）となりますが、フローの検証は可能です。

## 使用方法

通常、ローカル環境で `docker compose` プロファイルや環境変数 `RUN_MODE=cli` を指定して起動します。

```python
# saint_graph/config.py での自動設定例
# RUN_MODE=cli の場合、URL は http://body-cli:8000 になります
```

## API リファレンス

Streamer モードと共通のエンドポイントを提供します：
- `POST /api/speak`
- `POST /api/change_emotion`
- `GET /api/comments`
- `POST /api/broadcast/start`
- `POST /api/broadcast/stop`
- `POST /api/queue/wait` (CLI では即時復帰)
