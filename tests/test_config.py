"""Tests for the Config module."""
import os
import pytest
from unittest.mock import patch

from src.api_gateway_lambda.config import Config


class TestConfig:
    """Test cases for the Config class."""

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_access_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
            'AWS_REGION': 'us-west-2',
            'API_GATEWAY_ID': 'test_api_id',
            'LAMBDA_FUNCTION_NAME': 'test_lambda_function'
        }):
            config = Config()
            
            assert config.aws_access_key_id == 'test_access_key'
            assert config.aws_secret_access_key == 'test_secret_key'
            assert config.aws_region == 'us-west-2'
            assert config.api_gateway_id == 'test_api_id'
            assert config.lambda_function_name == 'test_lambda_function'

    def test_init_with_default_values(self):
        """Test initialization with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            assert config.aws_access_key_id is None
            assert config.aws_secret_access_key is None
            assert config.aws_region == 'us-east-1'
            assert config.api_gateway_id == '5321hipmwk'
            assert config.lambda_function_name == 'lambda-pg_api_metadata'

    def test_get_boto3_config_with_credentials(self):
        """Test get_boto3_config with credentials."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_access_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
            'AWS_REGION': 'us-west-2'
        }):
            config = Config()
            boto3_config = config.get_boto3_config()
            
            assert boto3_config['region_name'] == 'us-west-2'
            assert boto3_config['aws_access_key_id'] == 'test_access_key'
            assert boto3_config['aws_secret_access_key'] == 'test_secret_key'

    def test_get_boto3_config_without_credentials(self):
        """Test get_boto3_config without credentials."""
        with patch.dict(os.environ, {
            'AWS_REGION': 'us-west-2'
        }, clear=True):
            config = Config()
            boto3_config = config.get_boto3_config()
            
            assert boto3_config['region_name'] == 'us-west-2'
            assert 'aws_access_key_id' not in boto3_config
            assert 'aws_secret_access_key' not in boto3_config
