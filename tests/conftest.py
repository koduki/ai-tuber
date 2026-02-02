import pytest
import asyncio
import os
from typing import List, Optional
from google.genai import types

class MockGemini:
    def __init__(self, responses: List[types.Content] = None):
        self.responses = responses or []
        self.call_count = 0

    async def generate_content_async(self, req, stream=True):
        if self.call_count < len(self.responses):
            content = self.responses[self.call_count]
            self.call_count += 1
            
            # Simulate streaming
            # For simplicity, we just return one chunk with the whole content
            class MockChunk:
                def __init__(self, content, partial=False):
                    self.content = content
                    self.partial = partial
            
            yield MockChunk(content, partial=False)
        else:
            # Empty response
            yield None

@pytest.fixture
def mock_gemini():
    return MockGemini()

@pytest.fixture
def sample_system_instruction():
    return "You are a test AI."

@pytest.fixture
def sample_tools():
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="speak",
                    description="Speak text",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "text": types.Schema(type="STRING")
                        },
                        required=["text"]
                    )
                )
            ]
        )
    ]

# Docker fixtures for E2E tests
@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "docker-compose.yml")

@pytest.fixture(scope="session")
def docker_compose_project_name():
    return "ai-tuber-e2e"
