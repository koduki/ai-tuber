# OBS コンポーネント

OBS コンポーネントは、AI Tuber の映像・音声出力を担う中核です。  
`obs_adapter.py` が Python 側から OBS を制御し、`obs-studio` コンテナがヘッドレス環境で OBS Studio を稼働させます。

---

## 1. アダプター (`obs_adapter.py`)

`obs_adapter.py` は OBS WebSocket (v5) を通じて、配信画面の制御・立ち絵の変更・音声再生を行うモジュールです。

### 主な役割

| 役割 | 説明 |
| :--- | :--- |
| **表情（立ち絵）の変更** | 指定された感情に合わせて、OBS 上のソースの表示・非表示を切り替えます |
| **音声再生のトリガー** | `voice_adapter.py` で生成されたファイルのパスを OBS のメディアソースにセットし、再生を開始します |
| **配信・録画制御** | YouTube から取得したストリームキーの設定や、配信の開始・停止を制御します |

### 接続管理

シングルトン的に `ws_client` を保持し、呼び出しのたびに接続状態をチェック・再接続を試みる堅牢な設計になっています。

### 感情とソースのマッピング

`EMOTION_MAP` によって、API で指定された感情を OBS 内のソース名に変換します。

| API 感情値 | OBS ソース名 |
| :--- | :--- |
| `neutral` | `normal` |
| `happy` | `joyful` |
| `sad` | `sad` |
| `angry` | `angry` |

> **注意**: OBS のシーンコレクション内で、これらの名前のソース（画像やグループ）が定義されている必要があります。

### 主要な関数

#### `set_visible_source(emotion: str)`
指定された感情に対応するソースを表示し、それ以外の感情ソースを非表示にします。

#### `refresh_media_source(source_name: str, file_path: str)`
メディアソース（通常は `voice` ソース）のファイルパスを更新し、`Restart` アクションを実行して音声を再生します。  
> **重要**: OBS がファイルを読み込めるよう、**絶対パス**で指定する必要があります。

#### `start_streaming(stream_key: str)`
YouTube から渡されたストリームキーをセットし、配信を開始します。

### 環境変数

| 変数名 | 説明 | デフォルト値 |
| :--- | :--- | :--- |
| `OBS_HOST` | OBS Studio のホスト名 | `obs-studio` |
| `OBS_PORT` | OBS WebSocket のポート | `4455` |
| `OBS_PASSWORD` | WebSocket のパスワード | (なし) |

---

## 2. コンテナ構成 (`src/body/streamer/obs/`)

ヘッドレス環境（GPU 搭載の GCE インスタンス等）で OBS Studio を動作させるための専用 Docker コンテナです。

### ファイル構成

```
src/body/streamer/obs/
├── Dockerfile            # コンテナイメージ定義
├── supervisord.conf      # プロセスマネージャ設定
├── start_obs.sh          # OBS 起動スクリプト
├── download_assets.py    # アセットダウンロードスクリプト
├── apps                  # Fluxbox アプリ設定
└── config/               # OBS 設定ファイル群
    ├── global.ini
    ├── fluxbox/init
    └── basic/
        ├── profiles/Untitled/basic.ini
        └── scenes/Untitled.json
```

### `Dockerfile`

`nvidia/cuda:11.8.0-runtime-ubuntu22.04` をベースイメージとして使用します。  
GPU を活用した映像エンコードのために `NVIDIA_DRIVER_CAPABILITIES=all` を設定した上で、以下をインストールします：

| カテゴリ | パッケージ |
| :--- | :--- |
| 配信ソフト | `obs-studio` (PPA 経由) |
| 仮想ディスプレイ | `xvfb`, `fluxbox` |
| VNC / Web UI | `x11vnc`, `novnc`, `websockify` |
| 音声 | `pulseaudio` |
| OpenGL | `libegl1-mesa`, `libgl1-mesa-dri`, `libgl1-mesa-glx` 等 |
| スクリプト実行 | `python3`, `google-cloud-storage` |

### `supervisord.conf` — プロセス管理

コンテナ起動後、以下のプロセスを **priority 順** に管理します：

| priority | プロセス名 | コマンド | 役割 |
| :---: | :--- | :--- | :--- |
| 5 | `pulseaudio` | `pulseaudio --start` | 音声サーバー（OBS の音声出力に必要） |
| 10 | `xvfb` | `Xvfb :99 -screen 0 1920x1280x24` | 仮想ディスプレイ（DISPLAY :99） |
| 20 | `fluxbox` | `fluxbox -display :99` | ウィンドウマネージャ |
| 30 | `x11vnc` | `x11vnc -display :99 -rfbport 5900` | VNC サーバー（Port 5900） |
| 40 | `novnc` | `launch.sh --listen 8080 --vnc localhost:5900` | ブラウザ用 Web UI（Port **8080**） |
| 45 | `download-assets` | `python3 /app/download_assets.py` | アセット取得（一度だけ実行、`autorestart=false`） |
| 50 | `obs` | `start_obs.sh` | OBS Studio 本体（アセット待機後に起動） |

### `start_obs.sh` — OBS 起動スクリプト

OBS 本体を起動する前に以下の前処理を行います：

1. 前回の異常終了で残った **ロックファイルを削除**（`*.lock`, `.obs_websocket_lock`）
2. `/app/assets/.assets_ready` が作成されるまで **最大 120 秒ポーリング待機**
3. `QT_QPA_PLATFORM=xcb` を設定し、`obs --disable-shutdown-check` を実行

---

## 3. OBS 設定ファイル (`config/`)

コンテナビルド時に、以下の設定が `/root/.config/obs-studio/` に配置されます：

| ファイル | 説明 |
| :--- | :--- |
| `global.ini` | OBS の全体設定 |
| `basic/profiles/Untitled/basic.ini` | 録画設定、エンコーダ設定など |
| `basic/scenes/Untitled.json` | シーン構成。`normal`, `joyful`, `sad`, `angry` のソースを含む |
| `plugin_config/obs-websocket/config.json` | **重要**: WebSocket Server を有効化（Port 4455）し、認証なしで接続を許可 |

---

## 4. アセットダウンロードの流れ (`download_assets.py`)

OBS が起動する前に、クラウドストレージ（GCS / ローカル）からキャラクター画像や BGM を動的に取得します。  
`supervisord` によって `download-assets` と `obs` は並行して起動されますが、`start_obs.sh` がマーカーファイルを待機することで、アセットが揃ってから OBS が起動する順序が保証されます。

```mermaid
flowchart TD
    A([supervisord 起動]) --> B[download-assets プロセス起動]
    A --> C[start_obs.sh 起動]

    B --> D[StorageClient 初期化\nSTORAGE_TYPE: filesystem / gcs]
    D --> E{初期化成功?}
    E -- 失敗 --> F([exit 1])
    E -- 成功 --> G[アセット一覧取得\nprefix: mind/{CHARACTER_NAME}/assets/]
    G --> H{アセットが存在?}
    H -- なし --> I[警告ログ出力]
    H -- あり --> J[各ファイルを /app/assets/ にダウンロード]
    I --> K
    J --> K[マーカーファイル作成\n/app/assets/.assets_ready]
    K --> L{全ファイル失敗?}
    L -- Yes --> F
    L -- No --> M([download-assets 完了])

    C --> N[ロックファイル削除]
    N --> O{.assets_ready を検知?}
    O -- 未検知 --> P[1秒待機]
    P --> Q{120秒超過?}
    Q -- Yes --> F
    Q -- No --> O
    O -- 検知 --> R[OBS Studio 起動\nobs --disable-shutdown-check]
    R --> S([OBS 稼働中])
```

---

## 5. トラブルシューティング

| 症状 | 確認ポイント |
| :--- | :--- |
| **画面が真っ暗** | Xvfb が正常に起動しているか、NVIDIA ドライバが正しく認識されているかを確認 |
| **WebSocket 接続エラー** | `obs-websocket` の `config.json` が正しく読み込まれているか、Port 4455 が開いているかを確認 |
| **アセットが足りない** | `download_assets` のログ（`/var/log/supervisor/download_assets.log`）を確認し、ストレージのパス構成が正しいかを確認 |
| **OBS が起動しない** | `start_obs.sh` のログ（`/var/log/supervisor/obs.log`）を確認し、120 秒以内にアセットが揃っているかを確認 |
