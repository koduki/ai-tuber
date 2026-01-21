# Ren (紅月れん) - Character Package

このディレクトリには、AITuber「紅月れん」の完全なキャラクターパッケージが含まれています。
プラグインとして追加・削除可能な構成になっています。

## ディレクトリ構成

```
data/mind/ren/
├── README.md           # このファイル
├── persona.md          # キャラクター設定（性格、口調、背景など）
├── system_prompts/     # システムプロンプト（ニュース読み、応答など）
│   ├── intro.md              # 配信開始時の挨拶
│   ├── news_reading.md       # ニュース読み上げ
│   ├── news_finished.md      # ニュース終了時
│   ├── closing.md            # 配信終了時
│   ├── retry_no_tool.md      # ツール未使用時の再指示
│   └── retry_final_response.md # 最終応答の再指示
└── assets/             # OBSで使用するアセット
    ├── ai_normal.png   # 通常表情
    ├── ai_joyful.png   # 喜び表情
    ├── ai_fun.png      # 楽しい表情
    ├── ai_sad.png      # 悲しい表情
    └── ai_angry.png    # 怒り表情
```

## OBSシーン設定

OBSで以下のソースを設定してください：

### 画像ソース（表情）
- `normal` → `/app/assets/ai_normal.png`
- `joyful` → `/app/assets/ai_joyful.png`
- `fun` → `/app/assets/ai_fun.png`
- `sad` → `/app/assets/ai_sad.png`
- `angry` → `/app/assets/ai_angry.png`

### メディアソース（音声）
- `voice` → `/app/shared/audio/speech_0000.wav`

## 使用方法

1. コンテナ起動: `docker compose up`
2. VNCアクセス: `http://localhost:8080/vnc.html`
3. OBSでシーンとソースを手動設定
4. `body-desktop`サービスが自動的に表情を切り替え、音声を再生します

## カスタマイズ

- **persona.md**: キャラクターの性格や口調を変更
- **system_prompts/**: 各シーンのプロンプトをカスタマイズ
- **assets/**: 独自のアバター画像に差し替え

## 他のキャラクターの追加

新しいキャラクターを追加する場合は、`data/mind/`配下に同じ構造のディレクトリを作成してください：

```
data/mind/
├── ren/      # 紅月れん（既存）
└── aoi/      # 新キャラクター（例）
    ├── persona.md
    ├── system_prompts/
    └── assets/
```
