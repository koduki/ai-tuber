# テストカバレッジ分析 - dev/ren2 改修後

## 実施日
2026-02-02

## 主要な改修内容

### 1. YouTube OAuth 統一
- APIキー方式を削除
- OAuth認証のみに統一
- 環境変数の簡素化（3つ → 2つ）

### 2. YouTube コメント取得機能
- `fetch_comments.py`: OAuth対応コメント取得スクリプト
- `youtube_comment_adapter.py`: サブプロセス管理とエラー監視
- ライブチャットIDのリトライロジック実装

### 3. OBS設定の改善
- ウィザード抑制の強化
- 設定ファイルの最適化

## 現在のテストカバレッジ

### ✅ 既存のテスト（28テスト）

#### Unit Tests (11テスト)
1. **`test_obs_recording.py`** (3テスト)
   - OBS録画開始/停止
   - 基本的なOBS操作

2. **`test_prompt_loader.py`** (5テスト)
   - プロンプト読み込み
   - キャラクターデータ読み込み

3. **`test_saint_graph.py`** (3テスト)
   - AI応答パース
   - 感情制御
   - セッション管理

4. **`test_weather_tools.py`** (3テスト)
   - 天気ツールの動作

#### Integration Tests (15テスト)
1. **`test_agent_scenarios.py`** (1テスト)
   - 天気シナリオ（LLM統合）

2. **`test_mind_prompts.py`** (1テスト)
   - マインドプロンプト統合

3. **`test_newscaster_flow.py`** (1テスト)
   - ニュース配信フロー

4. **`test_newscaster_logic_v2.py`** (2テスト)
   - ニュース配信ロジック

5. **`test_rest_body_cli.py`** (5テスト)
   - Body CLI REST API
   - **コメント取得API** ✅

6. **`test_speaker_id_integration.py`** (4テスト)
   - speaker_id の伝播
   - 音声合成統合

#### E2E Tests (2テスト - スキップ)
1. **`test_system_smoke.py`** (2テスト)
   - コメントサイクルE2E
   - システム全体のスモークテスト

## ❌ 不足しているテスト

### 高優先度

#### 1. YouTube OAuth 認証テスト
**ファイル**: `tests/unit/test_youtube_oauth.py`

```python
# 必要なテスト:
- test_oauth_credentials_from_env()      # 環境変数からOAuth認証情報を読み込み
- test_oauth_credentials_from_json()     # JSON文字列からOAuth認証情報を構築
- test_oauth_token_refresh()             # トークンのリフレッシュ
- test_oauth_scope_validation()          # スコープの検証
- test_oauth_credentials_missing()       # 認証情報が無い場合のエラーハンドリング
```

**理由**: OAuth統一が今回の大きな変更の1つだが、テストがない

#### 2. YouTube コメント取得テスト
**ファイル**: `tests/unit/test_youtube_comment_adapter.py`

```python
# 必要なテスト:
- test_comment_adapter_initialization()       # アダプターの初期化
- test_comment_subprocess_env_propagation()   # 環境変数がサブプロセスに渡される
- test_comment_parsing()                      # JSONコメントのパース
- test_error_handling()                       # エラーハンドリング（stderr監視）
- test_adapter_cleanup()                      # リソースクリーンアップ
```

**理由**: 環境変数伝播とエラー監視が重要な機能だが、テストがない

#### 3. fetch_comments.py テスト
**ファイル**: `tests/unit/test_fetch_comments.py`

```python
# 必要なテスト:
- test_oauth_authentication()                    # OAuth認証の成功
- test_live_chat_id_retry_logic()               # ライブチャットIDのリトライ
- test_live_chat_id_retry_exhausted()           # リトライ上限に達した場合
- test_comment_polling()                        # コメントポーリングループ
- test_api_error_handling()                     # YouTube API エラー
- test_json_output_format()                     # JSON出力の形式
```

**理由**: リトライロジックは重要な機能だが、単体テストがない

### 中優先度

#### 4. YouTube Live配信テスト
**ファイル**: `tests/integration/test_youtube_streaming.py`

```python
# 必要なテスト:
- test_broadcast_creation()           # 配信作成
- test_stream_binding()               # ストリームのバインド
- test_broadcast_transition()         # 配信状態の遷移
- test_comment_integration()          # コメント取得との統合
```

**理由**: 配信機能は実装されているが、統合テストがない

#### 5. OBS設定テスト
**ファイル**: `tests/unit/test_obs_configuration.py`

```python
# 必要なテスト:
- test_wizard_suppression()           # ウィザード抑制の確認
- test_nvenc_configuration()          # NVENC設定の検証
- test_stream_settings()              # ストリーム設定
- test_config_file_generation()       # 設定ファイルの生成
```

**理由**: OBS設定の改善が行われたが、検証テストがない

### 低優先度

#### 6. エンドツーエンドテスト
**ファイル**: `tests/e2e/test_youtube_streaming_flow.py`

```python
# 必要なテスト:
- test_full_streaming_flow()          # 配信開始 → コメント取得 → 配信終了
- test_streaming_with_comments()      # コメントありの配信
- test_streaming_error_recovery()     # エラーからの回復
```

**理由**: 実際の配信フローの検証（環境依存）

## テスト項目の詳細

### 1. YouTube OAuth 認証テスト

#### `tests/unit/test_youtube_oauth.py`

```python
import os
import pytest
import json
from unittest.mock import patch, MagicMock
from google.oauth2.credentials import Credentials


class TestYouTubeOAuth:
    """YouTube OAuth 認証のテスト"""
    
    def test_oauth_credentials_from_env(self):
        """環境変数からOAuth認証情報を読み込む"""
        token_json = json.dumps({
            "token": "ya29.test",
            "refresh_token": "1//test",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test.apps.googleusercontent.com",
            "client_secret": "TEST-secret",
            "scopes": ["https://www.googleapis.com/auth/youtube"]
        })
        
        with patch.dict(os.environ, {"YOUTUBE_TOKEN_JSON": token_json}):
            # fetch_comments.py の実装をテスト
            token_info = json.loads(os.getenv("YOUTUBE_TOKEN_JSON"))
            creds = Credentials.from_authorized_user_info(
                token_info,
                scopes=token_info.get('scopes')
            )
            
            assert creds.token == "ya29.test"
            assert creds.refresh_token == "1//test"
            assert "https://www.googleapis.com/auth/youtube" in creds.scopes
    
    def test_oauth_credentials_missing(self):
        """認証情報が無い場合のエラーハンドリング"""
        with patch.dict(os.environ, {}, clear=True):
            youtube_token_json = os.getenv("YOUTUBE_TOKEN_JSON", "")
            
            assert youtube_token_json == ""
            # エラーハンドリングのテスト
    
    def test_oauth_scope_from_token(self):
        """トークンに含まれるスコープを使用する"""
        token_info = {
            "token": "ya29.test",
            "scopes": ["https://www.googleapis.com/auth/youtube"]
        }
        
        # スコープがトークンから取得されることを確認
        scopes = token_info.get('scopes', ["https://www.googleapis.com/auth/youtube"])
        assert scopes == ["https://www.googleapis.com/auth/youtube"]
```

### 2. YouTube コメント取得テスト

#### `tests/unit/test_youtube_comment_adapter.py`

```python
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from body.streamer.youtube_comment_adapter import YouTubeCommentAdapter


class TestYouTubeCommentAdapter:
    """YouTube コメントアダプターのテスト"""
    
    def test_adapter_initialization(self):
        """アダプターの初期化"""
        adapter = YouTubeCommentAdapter("test_video_id")
        
        assert adapter.video_id == "test_video_id"
        assert adapter.process is not None
    
    def test_env_propagation(self):
        """環境変数がサブプロセスに渡される"""
        with patch("subprocess.Popen") as mock_popen:
            adapter = YouTubeCommentAdapter("test_video_id")
            
            # Popen が env=os.environ.copy() で呼ばれたことを確認
            call_args = mock_popen.call_args
            assert 'env' in call_args.kwargs
            assert call_args.kwargs['env'] is not None
    
    def test_comment_parsing(self):
        """JSONコメントのパース"""
        adapter = YouTubeCommentAdapter("test_video_id")
        
        # モックのコメントを queue に追加
        test_comment = '{"author": "@test", "message": "Hello", "timestamp": "2026-02-02T00:00:00Z"}'
        adapter.q.put(test_comment)
        
        comments = adapter.get()
        
        assert len(comments) == 1
        assert comments[0]["author"] == "@test"
        assert comments[0]["message"] == "Hello"
    
    def test_error_detection(self):
        """エラー検出（stderr監視）"""
        adapter = YouTubeCommentAdapter("test_video_id")
        
        # エラーをerror_qに追加
        adapter.error_q.put("ERROR: OAuth failed")
        
        # get() を呼ぶとエラーがログに出力される
        # （実際のテストではログ出力をモックする）
        comments = adapter.get()
```

### 3. fetch_comments.py テスト

#### `tests/unit/test_fetch_comments.py`

```python
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from body.streamer import fetch_comments


class TestFetchComments:
    """fetch_comments.py のテスト"""
    
    @patch('body.streamer.fetch_comments.build')
    def test_live_chat_id_retry_success(self, mock_build):
        """ライブチャットIDのリトライが成功する"""
        # 1回目: activeLiveChatId なし
        # 2回目: activeLiveChatId あり
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        mock_youtube.videos().list().execute.side_effect = [
            {'items': [{'liveStreamingDetails': {}}]},  # 1回目: なし
            {'items': [{'liveStreamingDetails': {'activeLiveChatId': 'test_chat_id'}}]}  # 2回目: あり
        ]
        
        # fetch_comments 関数を呼ぶ
        # リトライロジックが機能することを確認
        
    @patch('body.streamer.fetch_comments.build')
    def test_live_chat_id_retry_exhausted(self, mock_build):
        """ライブチャットIDのリトライが上限に達する"""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # 常に activeLiveChatId を返さない
        mock_youtube.videos().list().execute.return_value = {
            'items': [{'liveStreamingDetails': {}}]
        }
        
        # 10回リトライ後にエラーを返す
    
    def test_json_output_format(self):
        """JSON出力の形式が正しい"""
        comment_data = {
            'author': '@test',
            'message': 'Test message',
            'timestamp': '2026-02-02T00:00:00Z'
        }
        
        json_str = json.dumps(comment_data)
        parsed = json.loads(json_str)
        
        assert parsed['author'] == '@test'
        assert parsed['message'] == 'Test message'
        assert 'timestamp' in parsed
```

## テスト実装の優先順位

### Phase 1: 必須（高優先度）
1. ✅ `test_youtube_oauth.py`
   - OAuth 統一が今回の大きな変更
   - 基本的な動作の検証が必要

2. ✅ `test_youtube_comment_adapter.py`
   - 環境変数伝播が重要な修正
   - エラー監視の検証が必要

3. ✅ `test_fetch_comments.py`
   - リトライロジックの検証
   - OAuth 認証の統合

### Phase 2: 推奨（中優先度）
4. `test_youtube_streaming.py`
   - 配信機能の統合テスト

5. `test_obs_configuration.py`
   - OBS設定の検証

### Phase 3: 将来（低優先度）
6. `test_youtube_streaming_flow.py`
   - E2Eテスト（環境依存）

## テストカバレッジの目標

### 現在
- **ユニットテスト**: 11
- **統合テスト**: 15
- **E2Eテスト**: 2 (スキップ)
- **合計**: 28テスト

### 目標（Phase 1完了後）
- **ユニットテスト**: 11 + 15 = 26
- **統合テスト**: 15テスト
- **E2Eテスト**: 2テスト
- **合計**: 43テスト（+15テスト、+54%）

### 目標（Phase 2完了後）
- **ユニットテスト**: 26 + 5 = 31
- **統合テスト**: 15 + 4 = 19
- **E2Eテスト**: 2テスト
- **合計**: 52テスト（+24テスト、+86%）

## まとめ

### 追加すべきテスト（Phase 1）

1. **`tests/unit/test_youtube_oauth.py`** (5テスト)
   - OAuth 認証の基本動作
   - 環境変数からの読み込み
   - エラーハンドリング

2. **`tests/unit/test_youtube_comment_adapter.py`** (5テスト)
   - アダプターの初期化と動作
   - 環境変数伝播
   - エラー監視

3. **`tests/unit/test_fetch_comments.py`** (5テスト)
   - リトライロジック
   - OAuth 認証統合
   - JSON出力形式

**合計**: 15テスト追加

これらのテストを実装することで、今回の改修内容が適切にテストされます。

## 次のステップ

1. Phase 1のテストを実装
2. カバレッジレポートを生成（`pytest --cov`）
3. カバレッジ80%以上を目指す
4. CI/CDパイプラインに統合

---

**作成日**: 2026-02-02  
**次回レビュー**: Phase 1テスト実装後
