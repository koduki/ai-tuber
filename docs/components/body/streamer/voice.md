# Voice モジュール (voice_adapter.py)

`voice_adapter.py` は、VOICEVOX Engine と連携して AI Tuber の音声を合成するためのアダプターモジュールです。

## 主な役割
1. **音声合成**: テキストを VOICEVOX API に送信し、WAV 形式の音声データを取得します。
2. **共有ボリュームへの保存**: 生成したファイルを、OBS がアクセス可能な `/app/shared/voice` ディレクトリに保存します。
3. **再生時間の計算**: 音声が途切れないよう、WAV ファイルのメタデータから正確な再生時間を算出します。

## 設定 (環境変数)
| 変数名 | 説明 | デフォルト値 |
| :--- | :--- | :--- |
| `VOICEVOX_HOST` | VOICEVOX サーバーのホスト名 | `voicevox` |
| `VOICEVOX_PORT` | VOICEVOX サーバーのポート | `50021` |

## 表情と話者のマッピング
`SPEAKER_MAP` により、感情（style）に応じた VOICEVOX の話者 ID を割り当てています。
- `neutral` / `normal`: ID 1
- `happy`: ID 2
- `sad`: ID 9
- `angry`: ID 6

## 主要な関数

### `generate_and_save(text: str, style: str, speaker_id: int)`
最も頻繁に呼ばれる高レベル関数です。
- **入力**: 合成したいテキスト、感情スタイル、または直接の話者 ID。
- **処理**: 音声生成から `/app/shared/voice/speech_XXXX.wav` への保存までを実行。
- **戻り値**: `(保存先パス, 再生秒数)` のタプル。

### `generate_speech(text, speaker_id)`
VOICEVOX API (`/audio_query` および `/synthesis`) を呼び出す低レベル関数です。

## 注意事項
- 音声ファイルは共有ディレクトリに保存されるため、Docker 構成時は Body コンポーネントと OBS コンポーネントで同じパスをマウントしている必要があります。
- ファイル名は `speech_{hash}.wav` の形式で生成されます。
