"""
Unit tests for PromptLoader functionality.
"""
import pytest
import json
import tempfile
from pathlib import Path
from saint_graph.prompt_loader import PromptLoader


def test_load_mind_config_success():
    """mind.jsonが存在する場合、正しく読み込まれる"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create temporary directory structure
        mind_dir = Path(tmpdir) / "data" / "mind" / "test_char"
        mind_dir.mkdir(parents=True)
        
        # Create mind.json with test data
        config = {"speaker_id": 42, "custom_field": "value"}
        (mind_dir / "mind.json").write_text(json.dumps(config))
        
        # Create persona.md to avoid errors
        (mind_dir / "persona.md").write_text("# Test Persona")
        
        # Create loader and override paths
        loader = PromptLoader("test_char")
        loader._mind_config_path = mind_dir / "mind.json"
        
        result = loader.load_mind_config()
        
        assert result == config
        assert result["speaker_id"] == 42
        assert result["custom_field"] == "value"


def test_load_mind_config_missing_file():
    """mind.jsonが存在しない場合、空の辞書を返す"""
    loader = PromptLoader("nonexistent")
    loader._mind_config_path = Path("/nonexistent/path/mind.json")
    
    result = loader.load_mind_config()
    
    assert result == {}
    assert isinstance(result, dict)


def test_load_mind_config_invalid_json():
    """不正なJSON形式の場合、エラーログを出して空の辞書を返す"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mind_dir = Path(tmpdir) / "data" / "mind" / "test_char"
        mind_dir.mkdir(parents=True)
        
        # Create invalid JSON file
        (mind_dir / "mind.json").write_text("{ invalid json }")
        
        loader = PromptLoader("test_char")
        loader._mind_config_path = mind_dir / "mind.json"
        
        result = loader.load_mind_config()
        
        assert result == {}


def test_load_mind_config_empty_json():
    """空のJSONオブジェクトの場合、空の辞書を返す"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mind_dir = Path(tmpdir) / "data" / "mind" / "test_char"
        mind_dir.mkdir(parents=True)
        
        (mind_dir / "mind.json").write_text("{}")
        
        loader = PromptLoader("test_char")
        loader._mind_config_path = mind_dir / "mind.json"
        
        result = loader.load_mind_config()
        
        assert result == {}


def test_load_mind_config_only_speaker_id():
    """speaker_idのみが定義されている場合"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mind_dir = Path(tmpdir) / "data" / "mind" / "test_char"
        mind_dir.mkdir(parents=True)
        
        config = {"speaker_id": 58}
        (mind_dir / "mind.json").write_text(json.dumps(config))
        
        loader = PromptLoader("test_char")
        loader._mind_config_path = mind_dir / "mind.json"
        
        result = loader.load_mind_config()
        
        assert result == {"speaker_id": 58}
        assert result["speaker_id"] == 58
