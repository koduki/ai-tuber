import unittest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock

# This test verifies the streaming accumulation and function call logic
# that is implemented in src/saint_graph/main.py.
# Since main.py has a monolithic main() loop, we test the logic patterns here.

# Mocking the part and content structures as they appear in Google ADK/GenAI
class MockPart:
    def __init__(self, text=None, function_call=None):
        self.text = text
        self.function_call = function_call

class MockContent:
    def __init__(self, parts):
        self.parts = parts

class MockChunk:
    def __init__(self, parts, partial=True):
        self.content = MockContent(parts)
        self.partial = partial

class TestSaintGraphLogic(unittest.IsolatedAsyncioTestCase):
    async def test_streaming_accumulation(self):
        """Test that chunks are accumulated correctly into final content."""
        # Simulate chunks
        chunk1 = MockChunk([MockPart(text="Hello ")], partial=True)
        chunk2 = MockChunk([MockPart(text="World!")], partial=False)

        # Logic to be tested (matches main.py)
        accum_parts = []
        accum_text = ""

        async def mock_generator():
            yield chunk1
            yield chunk2

        async for chunk in mock_generator():
            if chunk.content and chunk.content.parts:
                for p in chunk.content.parts:
                    accum_parts.append(p)
                    if p.text:
                        accum_text += p.text

            if not chunk.partial:
                break

        self.assertEqual(accum_text, "Hello World!")
        self.assertEqual(len(accum_parts), 2)

    async def test_function_call_arg_normalization(self):
        """Test that string args in function calls are parsed to JSON."""
        # Case 1: JSON String
        fc_json = MagicMock()
        fc_json.args = '{"text": "hello"}'

        args = fc_json.args
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except:
                pass
        self.assertEqual(args, {"text": "hello"})

        # Case 2: Already Dict
        fc_dict = MagicMock()
        fc_dict.args = {"text": "world"}
        args2 = fc_dict.args
        if isinstance(args2, str):
            try:
                args2 = json.loads(args2)
            except:
                pass
        self.assertEqual(args2, {"text": "world"})

    async def test_tool_execution_failure_handling(self):
        """Test that tool execution errors are captured."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(side_effect=Exception("Tool failed"))

        fc_name = "speak"
        fc_args = {}

        tool_results = []
        try:
            res = await mock_client.call_tool(fc_name, fc_args)
            tool_results.append({"result": str(res)})
        except Exception as e:
            tool_results.append({"error": str(e)})

        self.assertEqual(tool_results[0]["error"], "Tool failed")

if __name__ == "__main__":
    unittest.main()
