import asyncio
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# appディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from body.streamer import obs_adapter as obs

class TestOBSRecording(unittest.IsolatedAsyncioTestCase):
    @patch('body.streamer.obs_adapter.obs_requests')
    @patch('body.streamer.obs_adapter.obsws')
    @patch('body.streamer.obs_adapter.connect')
    async def test_start_recording(self, mock_connect, mock_obsws, mock_requests):
        mock_connect.return_value = True
        obs.ws_client = MagicMock()
        mock_requests.StartRecord = MagicMock()
        
        result = await obs.start_recording()
        
        self.assertTrue(result)
        obs.ws_client.call.assert_called()

    @patch('body.streamer.obs_adapter.obs_requests')
    @patch('body.streamer.obs_adapter.obsws')
    @patch('body.streamer.obs_adapter.connect')
    async def test_stop_recording(self, mock_connect, mock_obsws, mock_requests):
        mock_connect.return_value = True
        obs.ws_client = MagicMock()
        mock_requests.StopRecord = MagicMock()
        
        result = await obs.stop_recording()
        
        self.assertTrue(result)
        obs.ws_client.call.assert_called()

    @patch('body.streamer.obs_adapter.obs_requests')
    @patch('body.streamer.obs_adapter.obsws')
    @patch('body.streamer.obs_adapter.connect')
    async def test_get_record_status(self, mock_connect, mock_obsws, mock_requests):
        mock_connect.return_value = True
        obs.ws_client = MagicMock()
        mock_requests.GetRecordStatus = MagicMock()
        mock_response = MagicMock()
        mock_response.getOutputActive.return_value = True
        obs.ws_client.call.return_value = mock_response
        
        result = await obs.get_record_status()
        
        self.assertTrue(result)
        obs.ws_client.call.assert_called()

if __name__ == '__main__':
    unittest.main()
