# OBS設定バックポート完了報告

## 実施日
2026-02-02

## 背景
OBS Studio 30.x系で自動構成ウィザードが起動時に表示され、ヘッドレス環境での自動配信が開始できない問題が発生していました。

## 実施内容

### 1. GitHubからの設定バックポート
dev/ren2ブランチで動作実績のある以下の設定ファイルをバックポート：
- `global.ini`: グローバル設定（ウィザード抑制用の完全な設定）
- `basic.ini`: プロファイル設定（全必須セクションを含む）
- `Untitled.json`: シーン構成

### 2. 重要な変更点

#### global.ini
```ini
[General]
FirstRun=true                    # trueに変更
ShowConfigWizard=false
OBSVersion=30.2.3
Pre19Defaults=false
Pre21Defaults=false
Pre23Defaults=false
Pre24.1Defaults=false
# ... 多数の追加設定項目
```

- **追加項目**: 20項目以上のGeneral設定
- **新規セクション**: `[BasicWindow]`（30項目以上）, `[Video]`, `[Accessibility]`

#### basic.ini
```ini
[SimpleOutput]
StreamEncoder=nvenc              # ffmpeg_nvenc → nvenc に変更
RecEncoder=nvenc
Preset=p4
NVENCPreset2=p2                  # p5 → p2 に変更（高品質化）

[Stream1]                        # 新規追加（必須）
IgnoreRecommended=false
EnableMultitrackVideo=false
...

[AdvOut]                         # 新規追加（必須）
ApplyServiceSettings=true
...
```

- **エンコーダー名変更**: OBS 30.x系では `nvenc` を使用
- **必須セクション追加**: `[Stream1]`, `[AdvOut]`, `[Panels]`

### 3. 技術的知見

#### ウィザード表示の根本原因
OBS 30.x系は設定ファイルの完全性チェックが厳格化されており、以下が欠けているとウィザードを強制表示：
1. `global.ini` の `[BasicWindow]` セクション全項目
2. `basic.ini` の `[Stream1]` セクション
3. `basic.ini` の `[AdvOut]` セクション
4. `basic.ini` の `[Panels]` セクション

#### エンコーダー名の変更
- **OBS 29.x以前**: `ffmpeg_nvenc`（フルネーム）
- **OBS 30.x系**: `nvenc`（短縮形）

設定ファイルに古い名前を使用すると、エンコーダーが認識されず配信が開始できない可能性があります。

## 結果
✅ OBS起動時にウィザードが表示されなくなった  
✅ NVENC ハードウェアエンコーダーが正常に動作  
✅ YouTube Live配信が自動で開始可能  
✅ 接続リトライロジックと組み合わせ、高い安定性を実現

## 更新されたドキュメント
- `/app/docs/specs/obs-studio-configuration.md`: 完全書き換え
- `/app/docs/specs/body-streamer-architecture.md`: バージョン1.4.1に更新

## 参考
- [動作実績のある設定（GitHub dev/ren2）](https://github.com/koduki/ai-tuber/tree/dev/ren2/src/body/streamer/obs/config)
- OBS Studio 30.2.3
- NVIDIA NVENC SDK
