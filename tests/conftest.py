"""Pytest configuration file."""
import os
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Fixture to mock environment variables for all tests."""
    with patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'test_access_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
        'AWS_REGION': 'us-east-1',
        'API_GATEWAY_ID': '5321hipmwk',
        'LAMBDA_FUNCTION_NAME': 'lambda-pg_api_metadata'
    }):
        yield
