"""Tests for the LambdaClient module."""
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open

from src.api_gateway_lambda.lambda_client import LambdaClient
from src.api_gateway_lambda.config import Config


class TestLambdaClient:
    """Test cases for the LambdaClient class."""

    @pytest.fixture
    def mock_boto3_client(self):
        """Fixture for mocking boto3 client."""
        with patch('boto3.client') as mock_client:
            yield mock_client

    @pytest.fixture
    def lambda_client(self, mock_boto3_client):
        """Fixture for creating a LambdaClient instance."""
        # Configure the mock client
        mock_lambda = MagicMock()
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'lambda': mock_lambda
        }[service]
        
        # Create the client
        client = LambdaClient()
        
        # Add the mock client to the client for testing
        client._lambda_client = mock_lambda
        
        return client
        
    def test_init_with_profile_name(self, mock_boto3_client):
        """Test initialization with profile name."""
        # Configure the mock client
        mock_lambda = MagicMock()
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'lambda': mock_lambda
        }[service]
        
        # Create the client with a profile name
        client = LambdaClient(profile_name='latest')
        
        # Verify the profile name was passed to the Config
        assert client.config.profile_name == 'latest'
        
        # Verify boto3 client was called with the correct parameters
        mock_boto3_client.assert_called_once_with('lambda', **client.config.get_boto3_config())

    def test_invoke_lambda(self, lambda_client):
        """Test invoke_lambda method."""
        # Configure the mock
        mock_response = {
            'StatusCode': 200,
            'Payload': MagicMock()
        }
        mock_response['Payload'].read.return_value = json.dumps({'result': 'success'}).encode('utf-8')
        lambda_client.lambda_client.invoke.return_value = mock_response
        
        # Call the method
        result = lambda_client.invoke_lambda('test_function', {'key': 'value'})
        
        # Verify the result
        assert result == {'result': 'success'}
        
        # Verify the mock was called correctly
        lambda_client.lambda_client.invoke.assert_called_once_with(
            FunctionName='test_function',
            InvocationType='RequestResponse',
            Payload=json.dumps({'key': 'value'})
        )

    def test_invoke_lambda_with_default_function_name(self, lambda_client):
        """Test invoke_lambda method with default function name."""
        # Configure the mock
        mock_response = {
            'StatusCode': 200,
            'Payload': MagicMock()
        }
        mock_response['Payload'].read.return_value = json.dumps({'result': 'success'}).encode('utf-8')
        lambda_client.lambda_client.invoke.return_value = mock_response
        lambda_client.config.lambda_function_name = 'default_function'
        
        # Call the method
        result = lambda_client.invoke_lambda(payload={'key': 'value'})
        
        # Verify the result
        assert result == {'result': 'success'}
        
        # Verify the mock was called correctly
        lambda_client.lambda_client.invoke.assert_called_once_with(
            FunctionName='default_function',
            InvocationType='RequestResponse',
            Payload=json.dumps({'key': 'value'})
        )

    def test_invoke_lambda_with_default_payload(self, lambda_client):
        """Test invoke_lambda method with default payload."""
        # Configure the mock
        mock_response = {
            'StatusCode': 200,
            'Payload': MagicMock()
        }
        mock_response['Payload'].read.return_value = json.dumps({'result': 'success'}).encode('utf-8')
        lambda_client.lambda_client.invoke.return_value = mock_response
        
        # Call the method
        result = lambda_client.invoke_lambda('test_function')
        
        # Verify the result
        assert result == {'result': 'success'}
        
        # Verify the mock was called correctly
        lambda_client.lambda_client.invoke.assert_called_once_with(
            FunctionName='test_function',
            InvocationType='RequestResponse',
            Payload=json.dumps({})
        )

    def test_get_lambda_function_info(self, lambda_client):
        """Test get_lambda_function_info method."""
        # Configure the mock
        lambda_client.lambda_client.get_function.return_value = {
            'Configuration': {
                'FunctionName': 'test_function',
                'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:test_function'
            }
        }
        
        # Call the method
        result = lambda_client.get_lambda_function_info('test_function')
        
        # Verify the result
        assert result['Configuration']['FunctionName'] == 'test_function'
        assert result['Configuration']['FunctionArn'] == 'arn:aws:lambda:us-east-1:123456789012:function:test_function'
        
        # Verify the mock was called correctly
        lambda_client.lambda_client.get_function.assert_called_once_with(
            FunctionName='test_function'
        )

    def test_get_lambda_function_info_with_default_function_name(self, lambda_client):
        """Test get_lambda_function_info method with default function name."""
        # Configure the mock
        lambda_client.lambda_client.get_function.return_value = {
            'Configuration': {
                'FunctionName': 'default_function',
                'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:default_function'
            }
        }
        lambda_client.config.lambda_function_name = 'default_function'
        
        # Call the method
        result = lambda_client.get_lambda_function_info()
        
        # Verify the result
        assert result['Configuration']['FunctionName'] == 'default_function'
        
        # Verify the mock was called correctly
        lambda_client.lambda_client.get_function.assert_called_once_with(
            FunctionName='default_function'
        )
