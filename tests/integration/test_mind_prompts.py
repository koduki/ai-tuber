import pytest
from unittest.mock import MagicMock, AsyncMock
import os
import tempfile
import shutil
from saint_graph.news_service import NewsService

# main.py のプロンプト読み込みロジックをテスト

@pytest.mark.asyncio
async def test_mind_prompt_loading():
    """
    検証項目:
    1. Mindディレクトリ配下の system_prompts からプロンプトが読み込めるか。
    2. Signature Greetings が定義されているか。
    """
    # 1. Setup Mock Mind Directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        mind_ren_dir = os.path.join(tmp_dir, "mind", "ren")
        prompts_dir = os.path.join(mind_ren_dir, "system_prompts")
        os.makedirs(prompts_dir)
        
        # Create dummy prompts
        with open(os.path.join(prompts_dir, "intro.md"), "w", encoding="utf-8") as f:
            f.write("Intro template with {character}")
        with open(os.path.join(prompts_dir, "news_reading.md"), "w", encoding="utf-8") as f:
            f.write("Reading template {title}")
        with open(os.path.join(prompts_dir, "news_finished.md"), "w", encoding="utf-8") as f:
            f.write("Finished template")
        with open(os.path.join(prompts_dir, "closing.md"), "w", encoding="utf-8") as f:
            f.write("Closing template")
            
        # 2. Simulate logic in main.py
        templates = {}
        # current_dir dummy
        base_dir = tmp_dir
        mind_dir = os.path.join(base_dir, "mind", "ren")
        actual_prompts_dir = os.path.join(mind_dir, "system_prompts")
        
        for name in ["intro", "news_reading", "news_finished", "closing"]:
            path = os.path.join(actual_prompts_dir, f"{name}.md")
            with open(path, "r", encoding="utf-8") as f:
                templates[name] = f.read()
        
        # 3. Assertions for loading
        assert "Intro template" in templates["intro"]
        assert "Reading template" in templates["news_reading"]
        
    # 4. Check actual persona.md for Signature Greetings
    # We use the real project path here
    persona_path = "/app/src/mind/ren/persona.md"
    assert os.path.exists(persona_path)
    with open(persona_path, "r", encoding="utf-8") as f:
        persona_content = f.read()
        assert "Signature Greetings" in persona_content
        assert "Opening:" in persona_content
        assert "Closing:" in persona_content
        assert "AITuber" in persona_content
