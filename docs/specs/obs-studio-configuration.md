# OBS Studio 設定仕様書

**対象サービス**: obs-studio  
**バージョン**: OBS 30.2.3  
**最終更新**: 2026-01-21

---

## 概要

`obs-studio` コンテナは、VNC経由でアクセス可能なOBS Studioの実行環境を提供します。
WebSocket APIを通じて `body-streamer` から制御され、映像合成と配信エンコードを担当します。

---

## コンテナ構成

### ベースイメージ

```dockerfile
FROM ubuntu:22.04
```

### インストールパッケージ

| パッケージ | 用途 |
|-----------|------|
| `obs-studio` | 配信ソフトウェア本体 |
| `xvfb` | 仮想ディスプレイサーバー |
| `fluxbox` | 軽量ウィンドウマネージャー |
| `x11vnc` | VNCサーバー |
| `novnc` | WebベースVNCクライアント |
| `supervisor` | プロセス管理 |
| `pulseaudio` | 音声サブシステム |

### ポート公開

- `8080`: noVNC (HTTP) - ブラウザからGUIアクセス
- `4455`: OBS WebSocket - プログラムからの制御

---

## プロセス管理

### Supervisord 設定

起動順序:
1. Xvfb (仮想ディスプレイ)
2. Fluxbox (ウィンドウマネージャー)
3. x11vnc (VNCサーバー)
4. noVNC (Webクライアント)
5. OBS Studio

### OBS起動スクリプト (`start_obs.sh`)

```bash
#!/bin/bash
# ロックファイルのクリーンアップ
rm -f /root/.config/obs-studio/basic/scenes/*.lock
rm -f /root/.config/obs-studio/basic/profiles/*/*.lock
rm -f /root/.config/obs-studio/global.ini.lock
rm -f /root/.config/obs-studio/plugin_config/obs-websocket/.obs_websocket_lock

# OBS起動（Safe Mode無効化、詳細ログ有効）
exec obs --disable-shutdown-check --verbose
```

**重要なフラグ**:
- `--disable-shutdown-check`: Safe Modeダイアログを回避
- `--verbose`: 詳細ログ出力

---

## OBS設定ファイル

### ディレクトリ構造

```
/root/.config/obs-studio/
├── global.ini                    # グローバル設定
├── basic/
│   ├── profiles/
│   │   └── Untitled/
│   │       └── basic.ini         # プロファイル設定
│   └── scenes/
│       └── Untitled.json         # シーンコレクション
└── plugin_config/
    └── obs-websocket/
        └── config.json           # WebSocket設定
```

### global.ini

```ini
[General]
FirstRun=true       # 初回起動扱いにする（ウィザード表示を防ぐ）

[Basic]
Profile=Untitled
ProfileDir=Untitled
SceneCollection=Untitled
SceneCollectionFile=Untitled

[OBSWebSocket]
FirstLoad=false
ServerEnabled=true
ServerPort=4455
AlertsEnabled=false
AuthRequired=false  # 認証無効（内部ネットワークのみ）
```

### WebSocket設定 (`plugin_config/obs-websocket/config.json`)

```json
{
  "address": "0.0.0.0",
  "port": 4455,
  "enabled": true,
  "authentication_enabled": false,
  "server_enabled": true,
  "server_port": 4455,
  "auth_required": false,
  "first_load": false
}
```

---

## シーンコレクション仕様

### Scene: s001 (メインシーン)

#### ソース一覧

| ソース名 | タイプ | ファイルパス | 初期状態 | 用途 |
|---------|--------|------------|---------|------|
| `normal` | Image | `/app/assets/ai_normal.png` | 👁️ 表示 | 通常表情 |
| `joyful` | Image | `/app/assets/ai_joyful.png` | 👻 非表示 | 喜び表情 |
| `fun` | Image | `/app/assets/ai_fun.png` | 👻 非表示 | 楽しい表情 |
| `angry` | Image | `/app/assets/ai_angry.png` | 👻 非表示 | 怒り表情 |
| `BGM` | Media | `/app/assets/bgm.mp3` | 👁️ 表示 | BGM再生 (Monitor and Output) |
| `voice` | Media | `/app/shared/audio/speech_0000.wav` | 👁️ 表示 | AIの音声再生 (Monitor and Output) |

**注意**: `voice` メディアソースは `body-streamer` からの自動再生指令（Restart）によって制御されます。

---

## アセットファイル仕様

### 配置場所

コンテナ内: `/app/assets/`  
ホスト: `data/mind/ren/assets/`

### ファイル一覧

| ファイル名 | サイズ | 用途 |
|-----------|--------|------|
| `ai_normal.png` | 1.7MB | 通常表情 |
| `ai_joyful.png` | 1.8MB | 喜び表情 |
| `ai_fun.png` | 1.9MB | 楽しい表情 |
| `ai_angry.png` | 1.8MB | 怒り表情 |
| `ai_sad.png` | 2.1MB | 悲しい表情 |
| `bgm.mp3` | - | BGM |

### ビルド時のコピー

```dockerfile
COPY data/mind/ren/assets /app/assets
```

**重要**: アセットはビルド時にイメージに含まれます。変更時は再ビルドが必要です。

---

## WebSocket API使用例

### 接続

```python
from obswebsocket import obsws, requests as obs_requests

ws = obsws("obs-studio", 4455, "")
ws.connect()
```

### ソースの表示/非表示切り替え

```python
# すべてのアバターを非表示
for source in ["normal", "joyful", "fun", "angry"]:
    ws.call(obs_requests.SetSceneItemEnabled(
        sceneName="s001",
        sceneItemId=get_item_id(source),
        sceneItemEnabled=False
    ))

# 指定されたソースのみ表示
ws.call(obs_requests.SetSceneItemEnabled(
    sceneName="s001",
    sceneItemId=get_item_id("joyful"),
    sceneItemEnabled=True
))
```

### メディアソースのリフレッシュ

```python
ws.call(obs_requests.SetInputSettings(
    inputName="voice",
    inputSettings={
        "local_file": "/app/shared/audio/speech_1234.wav",
        "restart_on_activate": True
    }
))

# 再生を強制リスタート (WebSocket v5)
ws.call(obs_requests.TriggerMediaInputAction(
    inputName="voice",
    mediaAction="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
))
```

---

## 録画機能

### 録画設定

- **フォーマット**: MKV (デフォルト)
- **出力パス**: `/config/recordings/` (コンテナ内)
- **エンコーダ**: x264

### 制御 API (WebSocket)

`body-desktop` から以下のリクエストを使用して録画を制御します。

- `StartRecord`: 録画開始
- `StopRecord`: 録画停止
- `GetRecordStatus`: 録画ステータス（実行中かどうか）の取得

---

## VNCアクセス

### 接続方法

ブラウザで以下のURLにアクセス:
```
http://localhost:8080/vnc.html
```

### 初回セットアップ手順

1. VNCでOBS画面にアクセス
2. Missing Filesダイアログが表示される
3. 「Search Directory...」ボタンをクリック
4. `/app/assets/` ディレクトリを選択
5. 「Apply」をクリック
6. すべてのファイルが自動的にマッピングされる

### 手動でのソース追加

#### 音声ソースの追加 (voice)

1. Sources パネルで「+」をクリック
2. 「Media Source」を選択
3. 名前: `voice`
4. 設定:
   - Local File: `/app/shared/audio/speech_0000.wav`
   - Restart playback when source becomes active: ✅ ON
   - Close file when inactive: ✅ ON
5. オーディオの詳細プロパティ:
   - 音声モニタリング: 「モニターと出力」に設定

---

## トラブルシューティング

### OBSがクラッシュする (SIGABRT)

**症状**:
```
obs-studio-1 | INFO exited: obs (terminated by SIGABRT; not expected)
```

**原因**: 
- 不正なシーンコレクションJSON
- 存在しないファイルパスを参照
- システムトレイ関連のフラグ使用

**対処法**:
1. ロックファイルを削除（`start_obs.sh`で自動実行）
2. `--minimize-to-tray` フラグを削除
3. シーンコレクションJSONを検証

### WebSocketに接続できない

**症状**:
```
ERROR - Failed to connect to OBS: [Errno 111] Connection refused
```

**原因**: OBS WebSocketサーバーが起動していない

**対処法**:
1. OBSが完全に起動するまで待機（約5秒）
2. WebSocket設定を確認: `/root/.config/obs-studio/plugin_config/obs-websocket/config.json`
3. OBSログを確認: `docker compose logs obs-studio | grep websocket`

### アセットファイルが見つからない

**症状**: Missing Filesダイアログが表示され続ける

**原因**: ファイルパスが間違っている

**対処法**:
1. コンテナ内でファイルを確認: `docker compose exec obs-studio ls -la /app/assets/`
2. パスが正しいことを確認
3. VNCで手動マッピング

---

## パフォーマンス設定

### 推奨設定

- **Output Mode**: Simple
- **Video Bitrate**: 2500 Kbps
- **Encoder**: Software (x264)
- **Audio Bitrate**: 160 Kbps
- **Resolution**: 1280x720 @ 30fps

### リソース使用量

| リソース | 使用量 |
|---------|--------|
| CPU | 10-30% (1コア) |
| Memory | 500MB-1GB |
| Disk | 100MB (イメージ含まず) |

---

## セキュリティ設定

### WebSocket認証

本番環境では認証を有効化することを推奨:

```json
{
  "authentication_enabled": true,
  "auth_required": true
}
```

環境変数でパスワードを設定:
```bash
OBS_PASSWORD=your_secure_password
```

### ネットワーク分離

- WebSocketは内部ネットワーク（Docker network）のみでアクセス可能
- VNCは開発環境のみで公開（本番では無効化推奨）

---

## 今後の改善予定

### Short-term

- [ ] 自動シーン設定スクリプト
- [ ] アセット更新の簡素化（ホットリロード）
- [ ] 配信プリセットの追加

### Mid-term

- [ ] 複数シーン対応
- [ ] トランジション設定
- [ ] カスタムフィルター対応

### Long-term

- [ ] NDI出力対応
- [ ] バーチャルカメラ出力
- [ ] クラウドストレージ連携

---

## 参考資料

- [OBS Studio Documentation](https://obsproject.com/wiki/)
- [OBS WebSocket Protocol v5](https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md)
- [Fluxbox Configuration](http://fluxbox.org/help/)
- [noVNC Documentation](https://novnc.com/info.html)
