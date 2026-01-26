# キャラクターパッケージ仕様書

**概要**: プラグイン型キャラクター定義パッケージ  
**バージョン**: 1.1.0  
**最終更新**: 2026-01-26

---

## 目的

AITuberシステムでは、キャラクターごとの定義（ペルソナ、プロンプト、アセット）を1つのパッケージとして管理します。
これにより、キャラクターの追加・削除・切り替えが容易になります。

---

## パッケージ構造

### 標準ディレクトリレイアウト

```
data/mind/{character_name}/
├── README.md                    # パッケージ説明書
├── persona.md                   # キャラクター設定（AIの性格・口調）
├── system_prompts/              # シーン別システムプロンプト
│   ├── intro.md                # 配信開始時
│   ├── news_reading.md         # ニュース読み上げ
│   ├── news_finished.md        # ニュース終了時
│   └── closing.md              # 配信終了時
└── assets/                      # OBSアセット（画像・音声）
    ├── ai_normal.png           # 通常表情
    ├── ai_joyful.png           # 喜び表情
    ├── ai_fun.png              # 楽しい表情
    ├── ai_sad.png              # 悲しい表情
    ├── ai_angry.png            # 怒り表情
    └── bgm.mp3                 # BGM（オプション）
```

---

## ファイル仕様

### 1. persona.md
キャラクターの魂（口調・性格）を定義します。
- **感情タグの指示**: 現在のシステムでは、発話の先頭に `[emotion: <type>]` を付与するルールが `core_instructions.md` で定義されています。各キャラクタープロンプトはこのルールに従う必要があります。

### 2. system_prompts/
各配信シーンにおけるAIへの具体的な指示を定義します。

| ファイル名 | 用途 | 備考 |
|-----------|------|------|
| `intro.md` | 配信開始時の挨拶 | |
| `news_reading.md` | ニュースの音読と解説 | `{title}`, `{content}` が注入される |
| `news_finished.md` | ニュース読了後のリアクション | |
| `closing.md` | 配信終了時の挨拶 | |

※ 以前のバージョンで存在した `retry_*.md` は、リトライロジックの廃止に伴い不要となりました。

---

## 感情制御の仕組み

AIはテキスト出力の際に、以下のいずれかのタグを付与します。
- `[emotion: neutral]`
- `[emotion: joyful]`
- `[emotion: fun]`
- `[emotion: sad]`
- `[emotion: angry]`

システム側でこのタグをパースし、`assets/` 内の対応する画像への切り替え命令を OBS に発行します。

---

## 新しいキャラクターの追加手順

1. `data/mind/{new_character}/` ディレクトリを作成。
2. 上記構造に従って `persona.md` 等の Markdown ファイルを作成。
3. `assets/` に立ち絵画像を配置。
4. `docker-compose.yml` または 環境変数 `CHARACTER_NAME` を指定して再起動。
