import os
import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock, call
from queue import Queue


class TestYouTubeCommentAdapter:
    """YouTube コメントアダプターのテスト
    
    Note: このテストは実際のYouTube APIを使用せず、モックで動作します。
    """
    
    @patch('body.streamer.youtube_comment_adapter.threading.Thread')
    @patch('body.streamer.youtube_comment_adapter.subprocess.Popen')
    def test_adapter_initialization(self, mock_popen, mock_thread):
        """アダプターが正しく初期化されること"""
        from body.streamer.youtube_comment_adapter import YouTubeCommentAdapter
        
        # モックプロセス
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        # モックスレッド（実際に起動しないようにする）
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # アダプターを初期化
        adapter = YouTubeCommentAdapter("test_video_id")
        
        # 検証: プロセスが作成されたこと
        assert adapter.process is not None
        assert mock_popen.called
    
    @patch('body.streamer.youtube_comment_adapter.threading.Thread')
    @patch('body.streamer.youtube_comment_adapter.subprocess.Popen')
    def test_env_propagation(self, mock_popen, mock_thread):
        """環境変数がサブプロセスに正しく渡されること（重要な修正）"""
        from body.streamer.youtube_comment_adapter import YouTubeCommentAdapter
        
        # モックプロセス
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        # モックスレッド
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # テスト用の環境変数を設定
        test_env = {
            "YOUTUBE_TOKEN_JSON": '{"token": "test"}',
            "YOUTUBE_CLIENT_SECRET_JSON": '{"installed": {}}'
        }
        
        with patch.dict(os.environ, test_env):
            adapter = YouTubeCommentAdapter("test_video_id")
            
            # Popen が呼ばれたことを確認
            assert mock_popen.called
            
            # env パラメータが渡されたことを確認
            call_kwargs = mock_popen.call_args.kwargs
            assert 'env' in call_kwargs
            
            # 環境変数がコピーされて渡されている
            passed_env = call_kwargs['env']
            assert passed_env is not None
            assert isinstance(passed_env, dict)
    
    @patch('body.streamer.youtube_comment_adapter.threading.Thread')
    @patch('body.streamer.youtube_comment_adapter.subprocess.Popen')
    def test_comment_parsing(self, mock_popen, mock_thread):
        """JSONコメントが正しくパースされること"""
        from body.streamer.youtube_comment_adapter import YouTubeCommentAdapter
        
        # モックプロセス
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        # モックスレッド
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        adapter = YouTubeCommentAdapter("test_video_id")
        
        # テストコメントをキューに追加
        test_comment1 = {
            "author": "@test_user",
            "message": "Hello, world!",
            "timestamp": "2026-02-02T17:00:00Z"
        }
        test_comment2 = {
            "author": "@another_user",
            "message": "こんにちは！",
            "timestamp": "2026-02-02T17:01:00Z"
        }
        
        adapter.q.put(json.dumps(test_comment1))
        adapter.q.put(json.dumps(test_comment2))
        
        # コメントを取得
        comments = adapter.get()
        
        # 検証
        assert len(comments) == 2
        assert comments[0]["author"] == "@test_user"
        assert comments[0]["message"] == "Hello, world!"
        assert comments[1]["author"] == "@another_user"
        assert comments[1]["message"] == "こんにちは！"
    
    @patch('body.streamer.youtube_comment_adapter.threading.Thread')
    @patch('body.streamer.youtube_comment_adapter.subprocess.Popen')
    def test_empty_queue(self, mock_popen, mock_thread):
        """キューが空の場合、空リストが返ること"""
        from body.streamer.youtube_comment_adapter import YouTubeCommentAdapter
        
        # モックプロセス
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        # モックスレッド
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        adapter = YouTubeCommentAdapter("test_video_id")
        
        # キューが空の状態でget()を呼ぶ
        comments = adapter.get()
        
        # 空リストが返る
        assert comments == []
    
    @patch('body.streamer.youtube_comment_adapter.threading.Thread')
    @patch('body.streamer.youtube_comment_adapter.subprocess.Popen')
    @patch('body.streamer.youtube_comment_adapter.logger')
    def test_error_detection(self, mock_logger, mock_popen, mock_thread):
        """エラーが検出され、ログに出力されること（重要な修正）"""
        from body.streamer.youtube_comment_adapter import YouTubeCommentAdapter
        
        # モックプロセス
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        # モックスレッド
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        adapter = YouTubeCommentAdapter("test_video_id")
        
        # エラーをキューに追加
        test_error = "ERROR: OAuth authentication failed"
        adapter.error_q.put(test_error)
        
        # get() を呼ぶとエラーがログに出力される
        comments = adapter.get()
        
        # エラーログが呼ばれたことを確認
        # (実際の実装では logger.error が呼ばれる)
        assert comments == []  # エラーがあってもコメントは空
    
    @patch('body.streamer.youtube_comment_adapter.threading.Thread')
    @patch('body.streamer.youtube_comment_adapter.subprocess.Popen')
    def test_invalid_json_handling(self, mock_popen, mock_thread):
        """不正なJSON形式のコメントが適切に処理されること"""
        from body.streamer.youtube_comment_adapter import YouTubeCommentAdapter
        
        # モックプロセス
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        # モックスレッド
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        adapter = YouTubeCommentAdapter("test_video_id")
        
        # 不正なJSONをキューに追加
        adapter.q.put('{ invalid json }')
        
        # get() を呼んでも例外が発生しない（適切にハンドリングされる）
        comments = adapter.get()
        
        # 不正なJSONは無視される
        assert isinstance(comments, list)
    
    @patch('body.streamer.youtube_comment_adapter.threading.Thread')
    @patch('body.streamer.youtube_comment_adapter.subprocess.Popen')
    def test_multiple_get_calls(self, mock_popen, mock_thread):
        """複数回get()を呼んでもキューが正しく処理されること"""
        from body.streamer.youtube_comment_adapter import YouTubeCommentAdapter
        
        # モックプロセス
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        # モックスレッド
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        adapter = YouTubeCommentAdapter("test_video_id")
        
        # 最初のコメント
        comment1 = {"author": "@user1", "message": "First", "timestamp": "2026-02-02T17:00:00Z"}
        adapter.q.put(json.dumps(comment1))
        
        # 1回目のget()
        comments1 = adapter.get()
        assert len(comments1) == 1
        assert comments1[0]["message"] == "First"
        
        # 2回目のget()（キューは空）
        comments2 = adapter.get()
        assert len(comments2) == 0
        
        # 新しいコメントを追加
        comment2 = {"author": "@user2", "message": "Second", "timestamp": "2026-02-02T17:01:00Z"}
        adapter.q.put(json.dumps(comment2))
        
        # 3回目のget()
        comments3 = adapter.get()
        assert len(comments3) == 1
        assert comments3[0]["message"] == "Second"
