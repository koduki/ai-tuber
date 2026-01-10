import pytest
from unittest.mock import AsyncMock, MagicMock
from google.genai import types
from saint_graph.saint_graph import SaintGraph
from saint_graph import config as cfg

@pytest.mark.asyncio
async def test_history_limit(sample_system_instruction, sample_tools):
    # Setup
    mcp_client = MagicMock()
    model = MagicMock()
    sg = SaintGraph(mcp_client, sample_system_instruction, sample_tools, model=model)
    
    # Execute: Add more than limit
    # We alternate roles because consecutive messages of the same role are merged.
    for i in range(cfg.HISTORY_LIMIT + 5):
        role = "user" if i % 2 == 0 else "model"
        sg.add_history(types.Content(role=role, parts=[types.Part(text=f"msg {i}")]))
        
    # Verify
    # The history limit is 20. When we add 25 messages alternating roles:
    # 0:U, 1:M, 2:U, 3:M, ..., 19:M, 20:U, 21:M, 22:U, 23:M, 24:U
    # When HISTORY_LIMIT is 20, it keeps [5, 6, ..., 24] (length 20).
    # However, SaintGraph ensures history doesn't start with a 'model' role (if config.ai_role is model).
    # Since 5 is 'model' (5%2 == 1), it might pop it.
    
    assert len(sg.chat_history) <= cfg.HISTORY_LIMIT
    assert sg.chat_history[-1].parts[0].text == f"msg {cfg.HISTORY_LIMIT + 5 - 1}"

@pytest.mark.asyncio
async def test_process_turn_flow(mock_gemini, sample_system_instruction, sample_tools):
    # Setup Mock Responses
    # 1st response: call tool
    resp1 = types.Content(
        role="assistant",
        parts=[
            types.Part(
                function_call=types.FunctionCall(
                    name="speak",
                    args={"text": "Hello world"}
                )
            )
        ]
    )
    # 2nd response: final talk
    resp2 = types.Content(
        role="assistant",
        parts=[types.Part(text="I spoke hello.")]
    )
    mock_gemini.responses = [resp1, resp2]
    
    mcp_client = AsyncMock()
    mcp_client.call_tool.return_value = "Success"
    
    sg = SaintGraph(mcp_client, sample_system_instruction, sample_tools, model=mock_gemini)
    
    # Execute
    await sg.process_turn("Say hello")
    
    # Verify
    assert mock_gemini.call_count == 2
    mcp_client.call_tool.assert_called_once_with("speak", {"text": "Hello world"})
    
    # History check: User input -> AI Tool Call -> Tool Result -> AI Final Response
    assert len(sg.chat_history) == 4
    assert sg.chat_history[0].role == "user"
    assert sg.chat_history[1].role == "assistant"
    assert sg.chat_history[2].role == "user" # Tool result is added as user role by SaintGraph
    assert sg.chat_history[3].role == "assistant"

@pytest.mark.asyncio
async def test_tool_error_handling(mock_gemini, sample_system_instruction, sample_tools):
    # Setup
    resp1 = types.Content(
        role="assistant",
        parts=[
            types.Part(
                function_call=types.FunctionCall(
                    name="speak",
                    args={"text": "Fail me"}
                )
            )
        ]
    )
    mock_gemini.responses = [resp1, types.Content(role="assistant", parts=[types.Part(text="Oops")])]
    
    mcp_client = AsyncMock()
    mcp_client.call_tool.side_effect = Exception("Tool exploded")
    
    sg = SaintGraph(mcp_client, sample_system_instruction, sample_tools, model=mock_gemini)
    
    # Execute
    await sg.process_turn("Try to fail")
    
    # Verify
    # The turn should complete even if tool fails
    assert len(sg.chat_history) == 4
    assert "error" in sg.chat_history[2].parts[0].function_response.response
    assert "Tool exploded" in sg.chat_history[2].parts[0].function_response.response["error"]

@pytest.mark.asyncio
async def test_tool_argument_normalization(mock_gemini, sample_system_instruction, sample_tools):
    # Setup
    # Simulating a case where function_call has args as a string
    fc = MagicMock()
    fc.name = "speak"
    fc.args = '{"text": "normalized"}'
    
    # Use model_construct to bypass Pydantic validation
    part = types.Part.model_construct(function_call=fc)
    resp1 = types.Content.model_construct(role="assistant", parts=[part])
    
    mock_gemini.responses = [
        resp1, 
        types.Content.model_construct(role="assistant", parts=[types.Part.model_construct(text="Done")])
    ]
    
    mcp_client = AsyncMock()
    sg = SaintGraph(mcp_client, sample_system_instruction, sample_tools, model=mock_gemini)
    
    # Execute
    await sg.process_turn("Normalize me")
    
    # Verify: call_tool should receive a dict, not a string
    mcp_client.call_tool.assert_called_once_with("speak", {"text": "normalized"})
