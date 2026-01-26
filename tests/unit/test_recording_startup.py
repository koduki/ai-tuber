import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from src.saint_graph.main import _run_newscaster_loop

@pytest.mark.asyncio
async def test_recording_wait_before_speak():
    """
    Verifies that a wait is inserted after starting recording and before speaking the intro.
    """
    # Setup Mocks
    mock_saint_graph = MagicMock()
    mock_saint_graph.body.start_recording = AsyncMock(return_value="OK")
    mock_saint_graph.process_turn = AsyncMock()

    mock_news_service = MagicMock()

    templates = {"intro": "Hello"}

    # We need to mock _check_comments inside main module context
    with patch("src.saint_graph.main._check_comments", side_effect=BaseException("StopLoop")), \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

        # Order verification helper
        manager = MagicMock()
        manager.attach_mock(mock_saint_graph.body.start_recording, 'start_recording')
        manager.attach_mock(mock_sleep, 'sleep')
        manager.attach_mock(mock_saint_graph.process_turn, 'process_turn')

        try:
            await _run_newscaster_loop(mock_saint_graph, mock_news_service, templates)
        except BaseException as e:
            if str(e) != "StopLoop":
                raise e

        print("\nCall sequence:", manager.mock_calls)
        print("start_recording calls:", mock_saint_graph.body.start_recording.mock_calls)

        # Verify start_recording is called
        mock_saint_graph.body.start_recording.assert_awaited_once()

        # Find index of calls
        calls = manager.mock_calls
        start_rec_idx = -1
        process_turn_idx = -1
        sleep_idx = -1

        for i, c in enumerate(calls):
            if c[0] == 'start_recording':
                start_rec_idx = i
            elif c[0] == 'process_turn':
                process_turn_idx = i
            elif c[0] == 'sleep':
                if c.args == (3.0,) or c.args == (2.0,):
                     sleep_idx = i

        assert start_rec_idx != -1, "start_recording was not called"
        assert process_turn_idx != -1, "process_turn was not called"

        # This assertion simulates the bug fix check
        if sleep_idx == -1:
            # We expect this failure initially
            pytest.fail("No asyncio.sleep(2.0/3.0) called. Fix is missing.")

        assert sleep_idx > start_rec_idx, "Sleep called before recording start"
        assert sleep_idx < process_turn_idx, "Sleep called after process turn"

if __name__ == "__main__":
    asyncio.run(test_recording_wait_before_speak())
