import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from tools.weather.tools import get_weather

@pytest.mark.asyncio
async def test_get_weather_success():
    # Mock Geocoding Response
    geo_response = {
        "results": [{
            "latitude": 35.6895,
            "longitude": 139.6917,
            "name": "Tokyo"
        }]
    }
    
    # Mock Weather Response
    weather_response = {
        "current_weather": {
            "temperature": 15.0,
            "weathercode": 0
        },
        "daily": {
            "time": ["2026-01-10", "2026-01-11", "2026-01-12"],
            "temperature_2m_max": [18.0, 17.0, 16.0],
            "temperature_2m_min": [10.0, 9.0, 8.0],
            "weathercode": [0, 1, 2]
        }
    }

    # Setup the mock for httpx.AsyncClient
    with patch('httpx.AsyncClient') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        # Setup mock responses
        mock_res_geo = MagicMock()
        mock_res_geo.json.return_value = geo_response
        
        mock_res_weather = MagicMock()
        mock_res_weather.json.return_value = weather_response
        
        # Async mock for get
        mock_client.get = AsyncMock(side_effect=[mock_res_geo, mock_res_weather])

        # Call the tool
        result = await get_weather("Tokyo")
        
        assert "Tokyo" in result
        assert "晴天" in result  # 'Clear sky' in Japanese
        assert "15.0" in result
        assert "最高 18.0" in result  # 'Max' in Japanese

@pytest.mark.asyncio
async def test_get_weather_not_found():
    # Mock Geocoding Response (no results)
    geo_response = {"results": []}
    
    with patch('httpx.AsyncClient') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        mock_res_geo = MagicMock()
        mock_res_geo.json.return_value = geo_response
        
        # Async mock
        mock_client.get = AsyncMock(return_value=mock_res_geo)

        result = await get_weather("UnknownCity")
        assert "見つかりませんでした" in result  # 'not found' in Japanese

@pytest.mark.asyncio
async def test_get_weather_error():
    with patch('httpx.AsyncClient') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        # Async mock raising exception
        mock_client.get = AsyncMock(side_effect=Exception("Network Error"))

        result = await get_weather("Tokyo")
        assert "失敗" in result  # 'Failed' in Japanese
        assert "Network Error" in result
