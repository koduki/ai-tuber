"""
Tests to verify that streaming responses don't cause duplicate function calls.

This test suite specifically targets the bug where accumulating parts from
multiple streaming chunks caused function calls to be duplicated.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from google.genai import types
from saint_graph.saint_graph import SaintGraph


class MockStreamingChunk:
    """Simulates a streaming chunk from Gemini API."""
    def __init__(self, content, partial=True):
        self.content = content
        self.partial = partial
        self.error_code = None
        self.error_message = None


class MockGeminiWithMultipleChunks:
    """Mock Gemini that simulates progressive streaming with multiple chunks."""
    def __init__(self, chunks_per_response=3):
        self.responses = []
        self.call_count = 0
        self.chunks_per_response = chunks_per_response

    async def generate_content_async(self, req, stream=True):
        if self.call_count < len(self.responses):
            final_content = self.responses[self.call_count]
            self.call_count += 1
            
            # Simulate progressive streaming by sending the same content multiple times
            # This mimics what happens with real Gemini streaming where parts accumulate
            for i in range(self.chunks_per_response):
                is_final = (i == self.chunks_per_response - 1)
                yield MockStreamingChunk(final_content, partial=not is_final)
        else:
            # Empty response
            class EmptyChunk:
                partial = False
                content = None
            yield EmptyChunk()


@pytest.fixture
def mock_gemini_streaming():
    return MockGeminiWithMultipleChunks(chunks_per_response=3)


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
                ),
                types.FunctionDeclaration(
                    name="change_emotion",
                    description="Change emotion",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "emotion": types.Schema(type="STRING")
                        },
                        required=["emotion"]
                    )
                )
            ]
        )
    ]


@pytest.mark.asyncio
async def test_no_duplicate_function_calls_in_streaming(
    mock_gemini_streaming,
    sample_system_instruction,
    sample_tools
):
    """
    Test that function calls are NOT duplicated when processing streaming responses.
    
    This is a regression test for the bug where parts were accumulated from all chunks,
    causing function calls to appear multiple times in the final content.
    """
    # Setup: Response with two function calls
    resp1 = types.Content(
        role="assistant",
        parts=[
            types.Part(
                function_call=types.FunctionCall(
                    name="change_emotion",
                    args={"emotion": "happy"}
                )
            ),
            types.Part(
                function_call=types.FunctionCall(
                    name="speak",
                    args={"text": "Hello!"}
                )
            )
        ]
    )
    
    # Final response after tools
    resp2 = types.Content(
        role="assistant",
        parts=[types.Part(text="Done speaking.")]
    )
    
    mock_gemini_streaming.responses = [resp1, resp2]
    
    mcp_client = AsyncMock()
    mcp_client.call_tool.return_value = "Success"
    
    sg = SaintGraph(
        mcp_client,
        sample_system_instruction,
        sample_tools,
        model=mock_gemini_streaming
    )
    
    # Execute
    await sg.process_turn("Say hello")
    
    # Verify: Each tool should be called EXACTLY once, not multiple times
    assert mcp_client.call_tool.call_count == 2, \
        f"Expected 2 tool calls, got {mcp_client.call_tool.call_count}"
    
    # Verify the specific calls
    calls = [call.args for call in mcp_client.call_tool.call_args_list]
    assert ("change_emotion", {"emotion": "happy"}) in calls
    assert ("speak", {"text": "Hello!"}) in calls
    
    # Verify no duplicate calls
    call_list = mcp_client.call_tool.call_args_list
    assert len(call_list) == len(set(str(c) for c in call_list)), \
        "Duplicate function calls detected!"


@pytest.mark.asyncio
async def test_streaming_parts_not_accumulated(
    mock_gemini_streaming,
    sample_system_instruction,
    sample_tools
):
    """
    Test that parts from intermediate streaming chunks are not accumulated.
    
    Only the final chunk should be used to avoid duplication.
    """
    # Setup: Single function call
    resp1 = types.Content(
        role="assistant",
        parts=[
            types.Part(
                function_call=types.FunctionCall(
                    name="speak",
                    args={"text": "Test message"}
                )
            )
        ]
    )
    
    resp2 = types.Content(
        role="assistant",
        parts=[types.Part(text="Complete")]
    )
    
    mock_gemini_streaming.responses = [resp1, resp2]
    
    mcp_client = AsyncMock()
    mcp_client.call_tool.return_value = "Success"
    
    sg = SaintGraph(
        mcp_client,
        sample_system_instruction,
        sample_tools,
        model=mock_gemini_streaming
    )
    
    # Execute
    await sg.process_turn("Test")
    
    # Verify: Exactly one call to speak
    assert mcp_client.call_tool.call_count == 1
    mcp_client.call_tool.assert_called_once_with("speak", {"text": "Test message"})
    
    # Verify history structure - should have exactly 4 entries
    # 1. User input
    # 2. AI response with function call
    # 3. Function result (as user role)
    # 4. AI final response
    assert len(sg.chat_history) == 4
    
    # Verify the AI response (index 1) has exactly 1 part with function_call
    ai_response = sg.chat_history[1]
    assert len(ai_response.parts) == 1
    assert ai_response.parts[0].function_call is not None


@pytest.mark.asyncio
async def test_multiple_streaming_chunks_single_result(
    mock_gemini_streaming,
    sample_system_instruction,
    sample_tools
):
    """
    Test that receiving the same content in 3 chunks results in only 1 execution.
    
    This simulates the real-world scenario where Gemini sends progressive updates.
    """
    # Create a response with 2 function calls
    function_calls = [
        types.Part(
            function_call=types.FunctionCall(
                name="change_emotion",
                args={"emotion": "excited"}
            )
        ),
        types.Part(
            function_call=types.FunctionCall(
                name="speak",
                args={"text": "I'm excited!"}
            )
        )
    ]
    
    resp = types.Content(role="assistant", parts=function_calls)
    mock_gemini_streaming.responses = [
        resp,
        types.Content(role="assistant", parts=[types.Part(text="Done")])
    ]
    
    # Use a mock that sends 5 chunks instead of 3
    mock_gemini_streaming.chunks_per_response = 5
    
    mcp_client = AsyncMock()
    mcp_client.call_tool.return_value = "OK"
    
    sg = SaintGraph(
        mcp_client,
        sample_system_instruction,
        sample_tools,
        model=mock_gemini_streaming
    )
    
    # Execute
    await sg.process_turn("Get excited")
    
    # Critical assertion: Despite 5 chunks, should only call each tool once
    assert mcp_client.call_tool.call_count == 2, \
        f"Expected 2 calls (one per function), got {mcp_client.call_tool.call_count}. " \
        f"This indicates parts were accumulated from multiple chunks!"
    
    # Verify the calls
    call_names = [call.args[0] for call in mcp_client.call_tool.call_args_list]
    assert call_names.count("change_emotion") == 1, \
        "change_emotion was called more than once!"
    assert call_names.count("speak") == 1, \
        "speak was called more than once!"
