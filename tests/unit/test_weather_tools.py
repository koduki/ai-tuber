import pytest
from unittest.mock import patch, MagicMock
import json
from src.body.weather.tools import get_weather

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

    # Setup the mock for urlopen
    with patch('urllib.request.urlopen') as mock_urlopen:
        # First call for Geocoding
        mock_res_geo = MagicMock()
        mock_res_geo.read.return_value = json.dumps(geo_response).encode('utf-8')
        mock_res_geo.__enter__.return_value = mock_res_geo
        
        # Second call for Weather
        mock_res_weather = MagicMock()
        mock_res_weather.read.return_value = json.dumps(weather_response).encode('utf-8')
        mock_res_weather.__enter__.return_value = mock_res_weather
        
        mock_urlopen.side_effect = [mock_res_geo, mock_res_weather]

        # Call the tool
        result = await get_weather("Tokyo")
        
        assert "Tokyo" in result
        assert "Clear sky" in result
        assert "15.0" in result
        assert "Max 18.0" in result

@pytest.mark.asyncio
async def test_get_weather_not_found():
    # Mock Geocoding Response (no results)
    geo_response = {"results": []}
    
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_res = MagicMock()
        mock_res.read.return_value = json.dumps(geo_response).encode('utf-8')
        mock_res.__enter__.return_value = mock_res
        mock_urlopen.return_value = mock_res

        result = await get_weather("UnknownCity")
        assert "not found" in result

@pytest.mark.asyncio
async def test_get_weather_error():
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = Exception("Network Error")

        result = await get_weather("Tokyo")
        assert "Failed to get weather" in result
        assert "Network Error" in result
