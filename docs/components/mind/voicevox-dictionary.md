# VOICEVOX ユーザー辞書の管理

本システムでは、VOICEVOX GUI版などで作成したユーザー辞書（`user_dict.json`）を読み込ませる機能があります。
辞書データは「精神（Mind）」の一部として、キャラクターごとに管理されます。

## 辞書データの配置

### 1. 辞書ファイルの取得
VOICEVOX GUI版のユーザー辞書は、通常以下の場所に保存されています（Windowsの場合）。

```text
C:\Users\<ユーザー名>\AppData\Local\voicevox-engine\user_dict.json
```

### 2. キャラクターフォルダへの配置
取得した `user_dict.json` を、対象キャラクターの mind フォルダにコピーします。

```bash
data/mind/{character_name}/
├── mind.json
├── user_dict.json  <-- ここに配置
└── ...
```

### 3. 設定の確認
`data/mind/{character_name}/mind.json` に以下の設定が含まれていることを確認してください。

```json
{
    "speaker_id": 58,
    "voicevox_data_dir": "."
}
```
`voicevox_data_dir` に `.` を指定することで、そのキャラクターのフォルダ自体が VOICEVOX エンジンにマウントされ、中の辞書が読み込まれます。

## ローカル環境での反映
ファイルを配置した後、VOICEVOX コンテナを再起動することで設定が反映されます。

```bash
docker compose up -d voicevox
```

起動ログに以下のような表示があれば、辞書が正しく読み込まれています。
`reading ... user.dict_csv ... {単語数}`

## GCP (GCE) 環境での反映
クラウド環境で辞書を有効にするには、GCS（Cloud Storage）へのアップロードが必要です。

1. **GCSへのアップロード**:
   `user_dict.json` を以下のパスにアップロードしてください。
   `gs://{バケット名}/mind/{character_name}/user_dict.json`

2. **自動同期**:
   GCE インスタンスの起動時に、スタートアップスクリプトが自動的に GCS からファイルをダウンロードし、`/opt/ai-tuber/data/mind/{character_name}/` に配置します。

3. **権限設定**:
   VoiceVox コンテナのユーザーがファイルを読み込めるよう、スタートアップスクリプト内で自動的に `chmod -R 777` が適用されます。

## 注意事項
- ユーザー辞書に1つも単語が登録されていない場合、`user_dict.json` は作成されません。
- コンテナ内のマウント先は `/home/user/.local/share/voicevox-engine-dev` です。
- GCE 環境ではインスタンスメタデータの `character_name` に基づいて同期対象が決定されます。
