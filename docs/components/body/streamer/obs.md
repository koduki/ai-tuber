# OBS モジュール (obs_adapter.py)

`obs_adapter.py` は、OBS WebSocket (v5) を使用して、配信画面の制御、立ち絵の変更、音声の再生指示を行うモジュールです。

## 主な役割
1. **表情（立ち絵）の変更**: 指定された感情に合わせて、OBS 上のソースの表示・非表示を切り替えます。
2. **音声再生のトリガー**: `voice.py` で生成されたファイルのパスを OBS のメディアソースにセットし、再生を開始させます。
3. **配信・録画制御**: YouTube から取得したストリームキーの設定や、配信の開始・停止を制御します。

## 設定 (環境変数)
| 変数名 | 説明 | デフォルト値 |
| :--- | :--- | :--- |
| `OBS_HOST` | OBS Studio のホスト名 | `obs-studio` |
| `OBS_PORT` | OBS WebSocket のポート | `4455` |
| `OBS_PASSWORD` | WebSocket のパスワード | (なし) |

## 感情とソースのマッピング
`EMOTION_MAP` によって、API で指定された感情を OBS 内のソース名に変換します。
- `neutral` -> `normal`
- `happy` -> `joyful`
- `sad` -> `sad`
- `angry` -> `angry`
※ OBS のシーンコレクション内で、これらの名前のソース（画像やグループ）が定義されている必要があります。

## 主要な関数

### `set_visible_source(emotion: str)`
- **処理**: 指定された感情に対応するソースを表示し、それ以外の感情ソースを非表示にします。

### `refresh_media_source(source_name: str, file_path: str)`
- **処理**: メディアソース（通常は話者用の `voice` ソース）のファイルパスを更新し、`Restart` アクションを実行して音声を再生します。
- **重要**: OBS がファイルを読み込めるよう、絶対パスで指定する必要があります。

### `start_streaming(stream_key: str)`
- **処理**: YouTube から渡されたストリームキーをセットし、配信を開始します。

## 接続管理
- シングルトン的に `ws_client` を保持し、呼び出しのたびに接続状態をチェック・再接続を試みる堅牢な設計になっています。
