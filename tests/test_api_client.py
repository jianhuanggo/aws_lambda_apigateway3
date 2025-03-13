"""Tests for the ApiClient module."""
import json
import pytest
from unittest.mock import patch, MagicMock

from src.api_gateway_lambda.api_client import ApiClient
from src.api_gateway_lambda.config import Config


class TestApiClient:
    """Test cases for the ApiClient class."""

    @pytest.fixture
    def api_client(self):
        """Fixture for creating an ApiClient instance."""
        return ApiClient()
        
    def test_init_with_profile_name(self):
        """Test initialization with profile name."""
        # Create the client with a profile name
        client = ApiClient(profile_name='latest')
        
        # Verify the profile name was passed to the Config
        assert client.config.profile_name == 'latest'

    @patch('requests.request')
    def test_make_request_get(self, mock_request, api_client):
        """Test make_request method with GET request."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = {'result': 'success'}
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response
        
        # Call the method
        result = api_client.make_request('https://example.com/api')
        
        # Verify the result
        assert result == {'result': 'success'}
        
        # Verify the mock was called correctly
        mock_request.assert_called_once_with(
            method='GET',
            url='https://example.com/api',
            headers={'Content-Type': 'application/json'},
            params=None,
            data=None,
            timeout=30
        )

    @patch('requests.request')
    def test_make_request_post_with_json_data(self, mock_request, api_client):
        """Test make_request method with POST request and JSON data."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = {'result': 'success'}
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response
        
        # Call the method
        result = api_client.make_request(
            'https://example.com/api',
            method='POST',
            data={'key': 'value'}
        )
        
        # Verify the result
        assert result == {'result': 'success'}
        
        # Verify the mock was called correctly
        mock_request.assert_called_once_with(
            method='POST',
            url='https://example.com/api',
            headers={'Content-Type': 'application/json'},
            params=None,
            data=json.dumps({'key': 'value'}),
            timeout=30
        )

    @patch('requests.request')
    def test_make_request_with_custom_headers(self, mock_request, api_client):
        """Test make_request method with custom headers."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = {'result': 'success'}
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response
        
        # Call the method
        result = api_client.make_request(
            'https://example.com/api',
            headers={'Authorization': 'Bearer token'}
        )
        
        # Verify the result
        assert result == {'result': 'success'}
        
        # Verify the mock was called correctly
        mock_request.assert_called_once_with(
            method='GET',
            url='https://example.com/api',
            headers={'Authorization': 'Bearer token'},
            params=None,
            data=None,
            timeout=30
        )

    @patch('requests.request')
    def test_make_request_with_params(self, mock_request, api_client):
        """Test make_request method with query parameters."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = {'result': 'success'}
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response
        
        # Call the method
        result = api_client.make_request(
            'https://example.com/api',
            params={'page': 1, 'limit': 10}
        )
        
        # Verify the result
        assert result == {'result': 'success'}
        
        # Verify the mock was called correctly
        mock_request.assert_called_once_with(
            method='GET',
            url='https://example.com/api',
            headers={'Content-Type': 'application/json'},
            params={'page': 1, 'limit': 10},
            data=None,
            timeout=30
        )

    @patch('requests.request')
    def test_make_request_with_non_json_response(self, mock_request, api_client):
        """Test make_request method with non-JSON response."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError('', '', 0)
        mock_response.text = 'Plain text response'
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response
        
        # Call the method
        result = api_client.make_request('https://example.com/api')
        
        # Verify the result
        assert result == {'text': 'Plain text response'}
