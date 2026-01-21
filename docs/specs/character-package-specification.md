# キャラクターパッケージ仕様書

**概要**: プラグイン型キャラクター定義パッケージ  
**バージョン**: 1.0.0  
**最終更新**: 2026-01-21

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
├── persona.md                   # キャラクター設定
├── system_prompts/              # システムプロンプト
│   ├── intro.md                # 配信開始時
│   ├── news_reading.md         # ニュース読み上げ
│   ├── news_finished.md        # ニュース終了時
│   ├── closing.md              # 配信終了時
│   ├── retry_no_tool.md        # ツール未使用時の再指示
│   └── retry_final_response.md # 最終応答の再指示
└── assets/                      # OBSアセット
    ├── ai_normal.png           # 通常表情
    ├── ai_joyful.png           # 喜び表情
    ├── ai_fun.png              # 楽しい表情
    ├── ai_sad.png              # 悲しい表情
    ├── ai_angry.png            # 怒り表情
    ├── bgm.mp3                 # BGM（オプション）
    └── *.png                   # その他アセット
```

---

## ファイル仕様

### 1. README.md

**目的**: パッケージの説明とセットアップ手順

**必須セクション**:
- パッケージ概要
- ディレクトリ構成
- OBSシーン設定手順
- 使用方法
- カスタマイズ方法

**例**:
```markdown
# {Character Name} - Character Package

このディレクトリには、AITuber「{Character Name}」の完全なキャラクターパッケージが含まれています。

## ディレクトリ構成
...

## OBSシーン設定
...
```

---

### 2. persona.md

**目的**: キャラクターの性格、口調、背景設定を定義

**必須項目**:
- キャラクター名
- 性格・性質
- 口調・話し方の特徴
- 背景設定
- 価値観・信念

**フォーマット**:
```markdown
# キャラクター設定: {Character Name}

## 基本情報
- 名前: 
- 年齢: 
- 性別: 
- 職業: 

## 性格
...

## 口調
...

## 背景
...
```

**使用箇所**: `saint-graph` のシステムインストラクションに統合

---

### 3. system_prompts/

**目的**: 各シーンで使用するプロンプトテンプレート

#### 必須プロンプト

| ファイル名 | 用途 | トリガー |
|-----------|------|---------|
| `intro.md` | 配信開始時の挨拶 | 配信スタート時 |
| `news_reading.md` | ニュース読み上げ | ニュース取得時 |
| `news_finished.md` | ニュース終了時 | 全ニュース読了時 |
| `closing.md` | 配信終了時 | 配信終了時 |
| `retry_no_tool.md` | ツール未使用時の再指示 | ツール呼び出し失敗時 |
| `retry_final_response.md` | 最終応答の再指示 | 応答生成失敗時 |

#### プロンプトフォーマット

```markdown
# {Prompt Name}

## 指示
{具体的な指示内容}

## 制約
- {制約1}
- {制約2}

## 出力例
{出力例}
```

**使用箇所**: `PromptLoader` で読み込み、ADKに渡される

---

### 4. assets/

**目的**: OBSで使用する画像・音声ファイル

#### 必須アセット

| ファイル名 | タイプ | サイズ推奨 | 用途 |
|-----------|--------|-----------|------|
| `ai_normal.png` | PNG | 1920x1080 | 通常表情 |
| `ai_joyful.png` | PNG | 1920x1080 | 喜び表情 |
| `ai_fun.png` | PNG | 1920x1080 | 楽しい表情 |
| `ai_angry.png` | PNG | 1920x1080 | 怒り表情 |
| `ai_sad.png` | PNG | 1920x1080 | 悲しい表情 |

#### オプションアセット

| ファイル名 | タイプ | 用途 |
|-----------|--------|------|
| `bgm.mp3` | MP3 | BGM |
| `background.png` | PNG | 背景画像 |
| `*.png` | PNG | カスタムアセット |

#### 画像仕様

- **フォーマット**: PNG (透過PNG推奨)
- **解像度**: 1920x1080 または 1080x1920
- **カラースペース**: sRGB
- **ファイルサイズ**: 5MB以下推奨

#### 音声仕様

- **フォーマット**: MP3 または WAV
- **サンプルレート**: 48kHz
- **ビットレート**: 320kbps (MP3)

---

## パッケージの配置

### ディレクトリパス

```
data/mind/{character_name}/
```

### 例: 紅月れん (ren)

```
data/mind/ren/
├── README.md
├── persona.md
├── system_prompts/
│   ├── intro.md
│   ├── news_reading.md
│   ├── news_finished.md
│   ├── closing.md
│   ├── retry_no_tool.md
│   └── retry_final_response.md
└── assets/
    ├── ai_normal.png
    ├── ai_joyful.png
    ├── ai_fun.png
    ├── ai_angry.png
    ├── ai_sad.png
    └── bgm.mp3
```

---

## パッケージの読み込み

### PromptLoader

```python
from saint_graph.prompt_loader import PromptLoader

loader = PromptLoader(character_name="ren")
persona = loader.load_system_instruction()  # persona.md + core_instructions.md
templates = loader.load_templates(["intro", "news_reading"])
```

### アセットのマウント

```dockerfile
# OBS Dockerfile
COPY data/mind/{character_name}/assets /app/assets
```

---

## 新しいキャラクターの追加手順

### 1. ディレクトリ作成

```bash
mkdir -p data/mind/{new_character}/system_prompts
mkdir -p data/mind/{new_character}/assets
```

### 2. ファイル作成

```bash
cd data/mind/{new_character}

# 必須ファイル
touch README.md
touch persona.md
touch system_prompts/intro.md
touch system_prompts/news_reading.md
touch system_prompts/news_finished.md
touch system_prompts/closing.md
touch system_prompts/retry_no_tool.md
touch system_prompts/retry_final_response.md
```

### 3. アセット配置

画像ファイルを `assets/` に配置

### 4. Dockerfile更新

```dockerfile
# src/body/obs/Dockerfile
- COPY data/mind/ren/assets /app/assets
+ COPY data/mind/{new_character}/assets /app/assets
```

### 5. saint-graph設定

```python
# 環境変数またはコード内で指定
CHARACTER_NAME = "{new_character}"
loader = PromptLoader(character_name=CHARACTER_NAME)
```

### 6. 再ビルド

```bash
docker compose up --build obs-studio
```

---

## 感情マッピング設定

### デフォルトマッピング (`body-desktop/obs.py`)

```python
EMOTION_MAP = {
    "neutral": "normal",
    "happy": "joyful",
    "joyful": "joyful",
    "fun": "fun",
    "sad": "normal",
    "sorrow": "normal",
    "angry": "angry",
}
```

### カスタムマッピング

キャラクターごとに異なる感情マッピングが必要な場合は、環境変数またはパッケージ内の設定ファイルで定義します。

**将来の拡張**:
```yaml
# data/mind/{character}/config.yaml
emotion_mapping:
  neutral: "normal"
  happy: "smile"
  angry: "mad"
  sad: "cry"
```

---

## バージョン管理

### パッケージバージョニング

推奨: セマンティックバージョニング (SemVer)

```
{character_name}-v{MAJOR}.{MINOR}.{PATCH}
```

例:
- `ren-v1.0.0`: 初期リリース
- `ren-v1.1.0`: プロンプト追加
- `ren-v2.0.0`: アセット刷新

### Git管理

```bash
# パッケージごとにコミットタグ
git tag -a ren-v1.0.0 -m "Release ren character package v1.0.0"
git push origin ren-v1.0.0
```

---

## テンプレートパッケージ

### 最小テンプレート

リポジトリに `data/mind/_template/` を用意し、新規キャラクター作成時にコピー:

```bash
cp -r data/mind/_template data/mind/{new_character}
```

---

## ライセンスとクレジット

### パッケージ内でのクレジット表記

**README.mdに記載**:
```markdown
## クレジット

- キャラクターデザイン: {Designer Name}
- 立ち絵イラスト: {Illustrator Name}
- BGM: {Composer Name}
- プロンプト設計: {Prompt Engineer Name}
```

### 利用規約

パッケージごとに `LICENSE.md` を追加可能

---

## パフォーマンス考慮事項

### アセットサイズの最適化

- 画像: WebP形式の検討（透過サポート）
- 音声: OGG Vorbis形式の検討

### ビルド時間の短縮

大容量アセットは外部ストレージ (S3等) から動的ダウンロードする仕組みを検討

---

## トラブルシューティング

### プロンプトが読み込まれない

**原因**: ファイル名やパスが間違っている

**確認**:
```python
from saint_graph.prompt_loader import PromptLoader
loader = PromptLoader(character_name="ren")
print(loader._mind_prompts_dir)  # パスを確認
```

### アセットがOBSで表示されない

**原因**: Dockerfileでコピーされていない、またはパスが間違っている

**確認**:
```bash
docker compose exec obs-studio ls -la /app/assets/
```

---

## 今後の拡張予定

### Short-term

- [ ] 環境変数によるキャラクター切り替え
- [ ] パッケージテンプレートの整備
- [ ] 検証スクリプト (`validate_package.py`)

### Mid-term

- [ ] YAML設定ファイル対応
  - `config.yaml`: 感情マッピング、環境設定
  - `voice.yaml`: VoiceVox speaker ID、スタイル設定
- [ ] 多言語対応（i18n）
- [ ] アセットの動的ダウンロード

### Long-term

- [ ] GUIベースのパッケージエディタ
- [ ] キャラクター間でのアセット共有機構
- [ ] クラウドベースのパッケージリポジトリ

---

## 参考資料

- [既存パッケージ例: ren](file:///app/data/mind/ren/README.md)
- [PromptLoader実装](file:///app/src/saint_graph/prompt_loader.py)
- [OBS アセット仕様](file:///app/docs/specs/obs-studio-configuration.md)
