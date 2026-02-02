# OBS Studio 設定仕様書

**対象サービス**: obs-studio  
**バージョン**: OBS 30.2.3  
**最終更新**: 2026-02-02

---

## 1. 概要

OBS Studio をヘッドレス環境(Docker コンテナ内)で実行し、WebSocket 経由で制御するための設定と構成です。本仕様は **dev/ren2 ブランチから実績のある設定をバックポート**し、NVIDIA NVENC ハードウェアエンコーダーによる安定配信を実現しています。

**重要**: OBS 30.x系では設定ファイルの完全性チェックが厳格化されており、不完全な設定ファイルは自動構成ウィザードを強制的に表示します。本仕様書の設定はウィザード回避に必要な全項目を含んでいます。

---

## 2. Docker環境構成

### 2.1 ベースイメージとGPUサポート

```dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=all,graphics,utility,video,display
ENV LIBGL_ALWAYS_SOFTWARE=1  # Xvfb互換性
```

### 2.2 主要パッケージ

| パッケージ | 用途 |
|-----------|------|
| `obs-studio` | 配信ソフトウェア本体（PPAから最新版） |
| `xvfb` | 仮想ディスプレイサーバー（`:99`） |
| `fluxbox` | 軽量ウィンドウマネージャー |
| `x11vnc` | VNCサーバー（ポート5900） |
| `novnc` | WebベースVNCクライアント（ポート8080） |
| `supervisor` | プロセス管理 |
| `pulseaudio` | 音声サブシステム |
| `libegl1-mesa`, `libgl1-mesa-glx` | OpenGL/EGLライブラリ |
| `pciutils`, `mesa-utils` | GPU診断ツール |

### 2.3 ポート公開

- `8080`: noVNC (HTTP) - ブラウザからGUI確認
- `4455`: OBS WebSocket - プログラムからの制御

---

## 3. OBS設定ファイル構成

### 3.1 global.ini（グローバル設定）

**場所**: `/root/.config/obs-studio/global.ini`

**目的**: ウィザード抑制と基本UI設定

**重要項目**:

```ini
[General]
FirstRun=true                    # 初回実行完了フラグ
ShowConfigWizard=false           # ウィザード強制非表示
OBSVersion=30.2.3                # バージョン情報
Pre19Defaults=false              # 過去バージョン設定フラグ
Pre21Defaults=false
Pre23Defaults=false
Pre24.1Defaults=false
MaxLogs=10
ProcessPriority=Normal
HotkeyFocusType=NeverDisableHotkeys
YtDockCleanupDone=true

[Basic]
Profile=Untitled                 # 使用プロファイル名
ProfileDir=Untitled
SceneCollection=Untitled         # 使用シーンコレクション
SceneCollectionFile=Untitled
ConfigOnNewProfile=true

[BasicWindow]
PreviewDisabled=true             # ヘッドレス用（プレビュー無効）
geometry=AdnQywAAAAAAAAAAAAAAAAAAB38AAAQM
PreviewEnabled=true
PreviewProgramMode=false
# ... 約30項目のUI設定が必要

[Video]
Renderer=OpenGL                  # レンダラー指定

[Accessibility]
# カラー設定（必須）
SelectRed=255
SelectGreen=65280
# ...
```

**注意**: `[BasicWindow]` セクションに多数のUI設定項目（`SceneDuplicationMode`, `SwapScenesMode`, `SnappingEnabled` など）が必要です。これらが欠けているとウィザードが表示されます。

---

### 3.2 basic.ini（プロファイル設定）

**場所**: `/root/.config/obs-studio/basic/profiles/Untitled/basic.ini`

**目的**: エンコーダーと出力設定

**必須セクションリスト**:
1. `[General]` - プロファイル名
2. `[Video]` - 解像度・FPS設定
3. `[Output]` - 出力モード
4. `[SimpleOutput]` - エンコーダー設定
5. `[Stream1]` - ストリーム詳細（**これが無いとウィザードが出る**）
6. `[AdvOut]` - 高度な出力設定（**必須**）
7. `[Audio]` - オーディオ設定
8. `[Panels]` - パネル設定

#### 映像設定（垂直配信用）

```ini
[Video]
BaseCX=720
BaseCY=1280
OutputCX=720
OutputCY=1280
FPSCommon=30
FPSNum=30
FPSDen=1
ColorFormat=NV12        # NVENC推奨フォーマット
ColorSpace=709
ColorRange=Partial
SdrWhiteLevel=300
HdrNominalPeakLevel=1000
```

#### エンコーダー設定（NVENC）

```ini
[SimpleOutput]
FilePath=/tmp
RecFormat=mkv
StreamEncoder=nvenc            # OBS 30.x系では 'nvenc' を使用
RecEncoder=nvenc               # 'ffmpeg_nvenc' ではない
VBitrate=2500
ABitrate=160
Preset=p4                      # 配信用プリセット（品質バランス）
NVENCPreset2=p2                # 録画用プリセット（より高品質）
StreamAudioEncoder=aac
RecAudioEncoder=aac
RecTracks=1
```

**エンコーダー名の注意**:
- OBS 30.x系: `nvenc`（短縮形）
- OBS 29.x以前: `ffmpeg_nvenc`（フル名）

#### ストリーム設定（必須）

```ini
[Stream1]
IgnoreRecommended=false
EnableMultitrackVideo=false
MultitrackVideoMaximumAggregateBitrateAuto=true
MultitrackVideoMaximumVideoTracksAuto=true
```

このセクションが無いと、OBSは「ストリーム設定が未完了」と判断してウィザードを表示します。

---

### 3.3 Untitled.json（シーン構成）

**場所**: `/root/.config/obs-studio/basic/scenes/Untitled.json`

**シーン構成** (`s001`):
- **BGM**: ffmpeg_source（`/app/assets/bgm.mp3`、ループ再生、音量2.3%）
- **voice**: ffmpeg_source（`/app/shared/voice/*.wav`、自動再起動）
- **normal**: image_source（`/app/assets/ai_normal.png`）
- **joyful**: image_source（`/app/assets/ai_joyful.png`）
- **fun**: image_source（`/app/assets/ai_fun.png`）
- **sad**: image_source（`/app/assets/ai_sad.png`）
- **angry**: image_source（`/app/assets/ai_angry.png`）

---

## 4. OBS WebSocket設定

**プロトコルバージョン**: v5（obs-websocket 5.x）

**接続情報**:
- ホスト: `obs-studio` (Dockerネットワーク内)
- ポート: `4455`
- 認証: 無効（`AuthRequired=false`）

**設定ファイル**: `/root/.config/obs-studio/plugin_config/obs-websocket/config.json`

```json
{
  "address": "0.0.0.0",
  "port": 4455,
  "enabled": true,
  "authentication_enabled": false,
  "server_enabled": true,
  "auth_required": false,
  "first_load": false
}
```

---

## 5. プロセス管理

### 5.1 Supervisord構成

**設定ファイル**: `/etc/supervisor/conf.d/supervisord.conf`

起動順序（priority順）:
1. `pulseaudio` (priority=5)
2. `xvfb` (priority=10) - 仮想ディスプレイ `:99`
3. `fluxbox` (priority=20) - ウィンドウマネージャー
4. `x11vnc` (priority=30) - VNCサーバー（ポート5900）
5. `novnc` (priority=40) - Web VNC（ポート8080）
6. `obs` (priority=50) - OBS Studio本体

### 5.2 OBS起動スクリプト

**場所**: `/usr/local/bin/start_obs.sh`

```bash
#!/bin/bash
# ロックファイルのクリーンアップ
rm -f /root/.config/obs-studio/basic/scenes/*.lock
rm -f /root/.config/obs-studio/basic/profiles/*/*.lock
rm -f /root/.config/obs-studio/global.ini.lock

# ヘッドレス用環境変数
export QT_QPA_PLATFORM=xcb

# global.ini を起動時に強制再生成（設定の確実な適用）
cat > /root/.config/obs-studio/global.ini << 'EOF'
[General]
FirstRun=true
ShowConfigWizard=false
# ... (完全な設定)
EOF

# OBS起動（ウィザード・アップデート抑制フラグ付き）
exec obs --disable-shutdown-check \
         --disable-updater \
         --disable-missing-files-check \
         --verbose 2>&1
```

**重要**: `start_obs.sh` 内で `global.ini` を動的生成することで、ビルドキャッシュの影響を受けにくくしています。

---

## 6. 接続リトライロジック

**実装**: `src/body/streamer/obs.py`

OBS WebSocket への接続は、コンテナ起動直後には失敗する可能性があるため、指数バックオフによるリトライを実装しています。

```python
async def connect(retries: int = 5, delay: float = 2.0) -> bool:
    for i in range(retries):
        try:
            ws_client = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
            ws_client.connect()
            return True
        except Exception as e:
            if i < retries - 1:
                await asyncio.sleep(delay)
    return False
```

**パラメータ**:
- 最大リトライ回数: 5回
- 初回待機時間: 2秒
- バックオフ方式: 指数（2秒 → 4秒 → 8秒...）

---

## 7. 配信開始手順

### 7.1 ストリーム設定の適用

```python
custom_settings = {
    "server": "rtmp://a.rtmp.youtube.com/live2",
    "key": stream_key,
    "use_auth": False
}

ws_client.call(obs_requests.SetStreamServiceSettings(
    streamServiceType="rtmp_custom",
    streamServiceSettings=custom_settings
))
```

### 7.2 開始コマンドと検証

```python
# 設定適用後1秒待機
await asyncio.sleep(1.0)

# 配信開始
ws_client.call(obs_requests.StartStream())

# 2秒後に状態確認
await asyncio.sleep(2.0)
status = ws_client.call(obs_requests.GetStreamStatus())
if status.outputActive or status.streamActive:
    logger.info("Verified: OBS is streaming")
```

---

## 8. トラブルシューティング

### 8.1 ウィザードが表示される場合

**原因**: 設定ファイルの不完全性

**確認項目**:
1. `global.ini` に `[BasicWindow]` セクションの全項目が存在するか
2. `basic.ini` に `[Stream1]` セクションが存在するか
3. `basic.ini` に `[AdvOut]` セクションが存在するか
4. `basic.ini` に `[Panels]` セクションが存在するか

**解決策**: dev/ren2ブランチの完全な設定をコピー

### 8.2 NVENC エンコーダーが認識されない

**確認コマンド**:
```bash
docker compose exec obs-studio nvidia-smi
docker compose exec obs-studio glxinfo | grep -i nvidia
```

**確認項目**:
- `StreamEncoder=nvenc` になっているか（`ffmpeg_nvenc` ではない）
- `ColorFormat=NV12` になっているか（NVENCはI420非推奨）
- Dockerfileに `ENV NVIDIA_VISIBLE_DEVICES=all` があるか
- docker-compose.ymlに `devices: nvidia` の設定があるか

### 8.3 配信が開始されない

**確認項目**:
1. OBS WebSocketに接続できているか（`obs.py` ログ確認）
2. `StartStream()` 後の検証ログで `outputActive=true` になっているか
3. YouTube ストリームキーが正しく設定されているか

**ログ確認**:
```bash
docker compose logs obs-studio | grep -i "stream"
docker compose logs body-streamer | grep "Verified"
```

---

## 9. 設定ファイルの完全性チェックリスト

ウィザード回避に必要な設定項目:

### global.ini
- [ ] `[General]` セクション（20項目以上）
- [ ] `[Basic]` セクション（4項目）
- [ ] `[BasicWindow]` セクション（30項目以上）
- [ ] `[Audio]` セクション
- [ ] `[Video]` セクション
- [ ] `[Accessibility]` セクション

### basic.ini
- [ ] `[General]` セクション
- [ ] `[Video]` セクション（10項目以上）
- [ ] `[Output]` セクション（10項目以上）
- [ ] `[SimpleOutput]` セクション（15項目以上）
- [ ] `[Stream1]` セクション（**必須**）
- [ ] `[AdvOut]` セクション（**必須**、40項目以上）
- [ ] `[Audio]` セクション（5項目以上）
- [ ] `[Panels]` セクション

---

## 10. 参考リンク

- [OBS Studio公式ドキュメント](https://obsproject.com/)
- [obs-websocket プロトコル仕様](https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md)
- [NVIDIA NVENC サポート](https://developer.nvidia.com/nvidia-video-codec-sdk)
- [実績のある設定（dev/ren2ブランチ）](https://github.com/koduki/ai-tuber/tree/dev/ren2/src/body/streamer/obs/config)
