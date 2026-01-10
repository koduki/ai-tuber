import pytest
from unittest.mock import MagicMock
from google.genai import types
from saint_graph.saint_graph import SaintGraph
from saint_graph.config import MODEL_NAME
from saint_graph.providers import get_provider_config

# Helper to get roles consistent with the model
provider_config = get_provider_config(MODEL_NAME)
AI_ROLE = provider_config.ai_role
USER_ROLE = provider_config.user_role

@pytest.fixture
def mock_mcp():
    return MagicMock()

@pytest.fixture
def saint_graph(mock_mcp):
    # SaintGraphの初期化（プロンプトやツールは最小限でOK）
    return SaintGraph(
        mcp_client=mock_mcp,
        system_instruction="Test instruction",
        tools=[]
    )

def test_add_history_merges_consecutive_user_turns(saint_graph):
    # 1つ目のユーザーメッセージ
    content1 = types.Content(role=USER_ROLE, parts=[types.Part(text="Hello")])
    saint_graph.add_history(content1)
    assert len(saint_graph.chat_history) == 1
    
    # 2つ目のユーザーメッセージ（連続）
    content2 = types.Content(role=USER_ROLE, parts=[types.Part(text="World")])
    saint_graph.add_history(content2)
    
    # マージされて要素数は1のまま、partsが2つになっているはず
    assert len(saint_graph.chat_history) == 1
    assert len(saint_graph.chat_history[0].parts) == 2
    assert saint_graph.chat_history[0].parts[0].text == "Hello"
    assert saint_graph.chat_history[0].parts[1].text == "World"

def test_add_history_merges_consecutive_model_turns(saint_graph):
    # 1つ目のモデルメッセージ
    content1 = types.Content(role=AI_ROLE, parts=[types.Part(text="I am")])
    saint_graph.add_history(content1)
    
    # 2つ目のモデルメッセージ（連続）
    content2 = types.Content(role=AI_ROLE, parts=[types.Part(text="AI")])
    saint_graph.add_history(content2)
    
    # マージされているはず
    assert len(saint_graph.chat_history) == 1
    assert len(saint_graph.chat_history[0].parts) == 2

def test_add_history_does_not_merge_different_roles(saint_graph):
    # ユーザー -> モデル
    saint_graph.add_history(types.Content(role=USER_ROLE, parts=[types.Part(text="U")]))
    saint_graph.add_history(types.Content(role=AI_ROLE, parts=[types.Part(text="M")]))
    
    # ロールが違うのでマージされず、要素数は2になるはず
    assert len(saint_graph.chat_history) == 2
    assert saint_graph.chat_history[0].role == USER_ROLE
    assert saint_graph.chat_history[1].role == AI_ROLE

def test_add_history_ignores_empty_parts(saint_graph):
    # 空のパーツを持つコンテンツを追加
    empty_content = types.Content(role=USER_ROLE, parts=[])
    saint_graph.add_history(empty_content)
    
    # 履歴に追加されないはず
    assert len(saint_graph.chat_history) == 0

def test_history_limit_removes_old_messages(saint_graph):
    # 履歴制限を一時的に小さく設定
    from saint_graph import config as sg_config
    original_limit = sg_config.HISTORY_LIMIT
    sg_config.HISTORY_LIMIT = 2
    
    try:
        saint_graph.add_history(types.Content(role=USER_ROLE, parts=[types.Part(text="1")]))
        saint_graph.add_history(types.Content(role=AI_ROLE, parts=[types.Part(text="2")]))
        saint_graph.add_history(types.Content(role=USER_ROLE, parts=[types.Part(text="3")]))
        saint_graph.add_history(types.Content(role=AI_ROLE, parts=[types.Part(text="4")]))
        
        # 1. [U1, A2, U3, A4] (Length 4)
        # 2. Limit 2 -> [U3, A4]
        # 3. Starts with User -> OK
        assert len(saint_graph.chat_history) == 2
        assert saint_graph.chat_history[0].parts[0].text == "3"
        assert saint_graph.chat_history[1].parts[0].text == "4"
    finally:
        sg_config.HISTORY_LIMIT = original_limit
