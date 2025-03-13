"""Tests for the ApiGatewayManager module."""
import json
import pytest
from unittest.mock import patch, MagicMock, call

from src.api_gateway_lambda.api_gateway_manager import ApiGatewayManager
from src.api_gateway_lambda.config import Config


class TestApiGatewayManager:
    """Test cases for the ApiGatewayManager class."""

    @pytest.fixture
    def mock_boto3_client(self):
        """Fixture for mocking boto3 client."""
        with patch('boto3.client') as mock_client:
            yield mock_client

    @pytest.fixture
    def api_gateway_manager(self, mock_boto3_client):
        """Fixture for creating an ApiGatewayManager instance."""
        # Configure the mock clients
        mock_apigateway = MagicMock()
        mock_lambda = MagicMock()
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'apigateway': mock_apigateway,
            'lambda': mock_lambda,
            'sts': MagicMock(get_caller_identity=MagicMock(return_value={'Account': '123456789012'}))
        }[service]
        
        # Create the manager
        manager = ApiGatewayManager()
        
        # Add the mock clients to the manager for testing
        manager._apigateway_client = mock_apigateway
        manager._lambda_client = mock_lambda
        
        return manager
        
    def test_init_with_profile_name(self, mock_boto3_client):
        """Test initialization with profile name."""
        # Configure the mock clients
        mock_apigateway = MagicMock()
        mock_lambda = MagicMock()
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'apigateway': mock_apigateway,
            'lambda': mock_lambda,
            'sts': MagicMock(get_caller_identity=MagicMock(return_value={'Account': '123456789012'}))
        }[service]
        
        # Create the manager with a profile name
        manager = ApiGatewayManager(profile_name='latest')
        
        # Verify the profile name was passed to the Config
        assert manager.config.profile_name == 'latest'
        
        # Verify boto3 client was called with the correct parameters
        mock_boto3_client.assert_any_call('apigateway', **manager.config.get_boto3_config())
        mock_boto3_client.assert_any_call('lambda', **manager.config.get_boto3_config())

    def test_create_api_gateway(self, api_gateway_manager):
        """Test create_api_gateway method."""
        # Configure the mock
        api_gateway_manager.api_gateway_client.create_rest_api.return_value = {'id': 'test_api_id'}
        
        # Call the method
        api_id = api_gateway_manager.create_api_gateway('TestAPI', 'Test API Description')
        
        # Verify the result
        assert api_id == 'test_api_id'
        
        # Verify the mock was called correctly
        api_gateway_manager.api_gateway_client.create_rest_api.assert_called_once_with(
            name='TestAPI',
            description='Test API Description',
            endpointConfiguration={
                'types': ['REGIONAL']
            }
        )

    def test_get_resources(self, api_gateway_manager):
        """Test get_resources method."""
        # Configure the mock
        api_gateway_manager.api_gateway_client.get_resources.return_value = {
            'items': [
                {'id': 'resource1', 'path': '/'},
                {'id': 'resource2', 'path': '/test'}
            ]
        }
        
        # Call the method
        resources = api_gateway_manager.get_resources('test_api_id')
        
        # Verify the result
        assert len(resources) == 2
        assert resources[0]['id'] == 'resource1'
        assert resources[1]['id'] == 'resource2'
        
        # Verify the mock was called correctly
        api_gateway_manager.api_gateway_client.get_resources.assert_called_once_with(
            restApiId='test_api_id'
        )

    def test_get_root_resource_id(self, api_gateway_manager):
        """Test get_root_resource_id method."""
        # Configure the mock
        api_gateway_manager.get_resources = MagicMock(return_value=[
            {'id': 'resource1', 'path': '/'},
            {'id': 'resource2', 'path': '/test'}
        ])
        
        # Call the method
        root_id = api_gateway_manager.get_root_resource_id('test_api_id')
        
        # Verify the result
        assert root_id == 'resource1'
        
        # Verify the mock was called correctly
        api_gateway_manager.get_resources.assert_called_once_with('test_api_id')

    def test_get_root_resource_id_not_found(self, api_gateway_manager):
        """Test get_root_resource_id method when root resource is not found."""
        # Configure the mock
        api_gateway_manager.get_resources = MagicMock(return_value=[
            {'id': 'resource2', 'path': '/test'}
        ])
        
        # Call the method and verify it raises an exception
        with pytest.raises(ValueError, match="Root resource not found for API Gateway test_api_id"):
            api_gateway_manager.get_root_resource_id('test_api_id')

    def test_create_resource(self, api_gateway_manager):
        """Test create_resource method."""
        # Configure the mocks
        api_gateway_manager.get_root_resource_id = MagicMock(return_value='root_id')
        api_gateway_manager.api_gateway_client.create_resource.return_value = {'id': 'new_resource_id'}
        
        # Call the method
        resource_id = api_gateway_manager.create_resource('test_api_id', 'test_path')
        
        # Verify the result
        assert resource_id == 'new_resource_id'
        
        # Verify the mocks were called correctly
        api_gateway_manager.get_root_resource_id.assert_called_once_with('test_api_id')
        api_gateway_manager.api_gateway_client.create_resource.assert_called_once_with(
            restApiId='test_api_id',
            parentId='root_id',
            pathPart='test_path'
        )

    def test_create_method(self, api_gateway_manager):
        """Test create_method method."""
        # Call the method
        api_gateway_manager.create_method('test_api_id', 'resource_id', 'GET')
        
        # Verify the mock was called correctly
        api_gateway_manager.api_gateway_client.put_method.assert_called_once_with(
            restApiId='test_api_id',
            resourceId='resource_id',
            httpMethod='GET',
            authorizationType='NONE',
            apiKeyRequired=False
        )

    def test_get_lambda_arn(self, api_gateway_manager):
        """Test get_lambda_arn method."""
        # Configure the mock
        api_gateway_manager.lambda_client.get_function.return_value = {
            'Configuration': {
                'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:test_function'
            }
        }
        
        # Call the method
        lambda_arn = api_gateway_manager.get_lambda_arn('test_function')
        
        # Verify the result
        assert lambda_arn == 'arn:aws:lambda:us-east-1:123456789012:function:test_function'
        
        # Verify the mock was called correctly
        api_gateway_manager.lambda_client.get_function.assert_called_once_with(
            FunctionName='test_function'
        )

    def test_integrate_with_lambda(self, api_gateway_manager):
        """Test integrate_with_lambda method."""
        # Configure the mocks
        api_gateway_manager.get_lambda_arn = MagicMock(
            return_value='arn:aws:lambda:us-east-1:123456789012:function:test_function'
        )
        api_gateway_manager.config.aws_region = 'us-east-1'
        
        # Call the method
        api_gateway_manager.integrate_with_lambda('test_api_id', 'resource_id', 'GET', 'test_function')
        
        # Verify the mocks were called correctly
        api_gateway_manager.get_lambda_arn.assert_called_once_with('test_function')
        
        api_gateway_manager.api_gateway_client.put_integration.assert_called_once_with(
            restApiId='test_api_id',
            resourceId='resource_id',
            httpMethod='GET',
            type='AWS',
            integrationHttpMethod='POST',
            uri='arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:test_function/invocations',
            contentHandling='CONVERT_TO_TEXT'
        )
        
        api_gateway_manager.api_gateway_client.put_integration_response.assert_called_once_with(
            restApiId='test_api_id',
            resourceId='resource_id',
            httpMethod='GET',
            statusCode='200',
            selectionPattern=''
        )
        
        api_gateway_manager.api_gateway_client.put_method_response.assert_called_once_with(
            restApiId='test_api_id',
            resourceId='resource_id',
            httpMethod='GET',
            statusCode='200',
            responseModels={
                'application/json': 'Empty'
            }
        )

    def test_deploy_api(self, api_gateway_manager):
        """Test deploy_api method."""
        # Configure the mock
        api_gateway_manager.api_gateway_client.create_deployment.return_value = {'id': 'deployment_id'}
        
        # Call the method
        deployment_id = api_gateway_manager.deploy_api('test_api_id', 'prod', 'Test deployment')
        
        # Verify the result
        assert deployment_id == 'deployment_id'
        
        # Verify the mock was called correctly
        api_gateway_manager.api_gateway_client.create_deployment.assert_called_once_with(
            restApiId='test_api_id',
            stageName='prod',
            description='Test deployment'
        )

    def test_get_invoke_url(self, api_gateway_manager):
        """Test get_invoke_url method."""
        # Configure the mock
        api_gateway_manager.config.aws_region = 'us-east-1'
        
        # Call the method
        url = api_gateway_manager.get_invoke_url('test_api_id', 'prod', 'test_resource')
        
        # Verify the result
        assert url == 'https://test_api_id.execute-api.us-east-1.amazonaws.com/prod/test_resource'
        
        # Test with empty resource path
        url = api_gateway_manager.get_invoke_url('test_api_id', 'prod')
        assert url == 'https://test_api_id.execute-api.us-east-1.amazonaws.com/prod'
        
        # Test with resource path that doesn't start with a slash
        url = api_gateway_manager.get_invoke_url('test_api_id', 'prod', 'test_resource')
        assert url == 'https://test_api_id.execute-api.us-east-1.amazonaws.com/prod/test_resource'

    def test_delete_resource(self, api_gateway_manager):
        """Test delete_resource method."""
        # Configure the mock
        api_id = "test_api_id"
        resource_id = "test_resource_id"
        
        # Call the method
        api_gateway_manager.delete_resource(api_id, resource_id)
        
        # Verify the mock was called correctly
        api_gateway_manager.api_gateway_client.delete_resource.assert_called_once_with(
            restApiId=api_id,
            resourceId=resource_id
        )
    
    def test_delete_method(self, api_gateway_manager):
        """Test delete_method method."""
        # Configure the mock
        api_id = "test_api_id"
        resource_id = "test_resource_id"
        http_method = "GET"
        
        # Call the method
        api_gateway_manager.delete_method(api_id, resource_id, http_method)
        
        # Verify the mock was called correctly
        api_gateway_manager.api_gateway_client.delete_method.assert_called_once_with(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method
        )
    
    def test_create_or_update_api_gateway(self, api_gateway_manager):
        """Test create_or_update_api_gateway method with no existing resource."""
        # Configure the mocks
        api_gateway_manager.config.api_gateway_id = 'existing_api_id'
        api_gateway_manager.get_api_gateway_by_id = MagicMock()
        api_gateway_manager.find_resource_by_path = MagicMock(return_value=None)
        api_gateway_manager.create_resource = MagicMock(return_value='new_resource_id')
        api_gateway_manager.create_method = MagicMock()
        api_gateway_manager.integrate_with_lambda = MagicMock()
        api_gateway_manager.add_lambda_permission = MagicMock()
        api_gateway_manager.deploy_api = MagicMock()
        api_gateway_manager.get_invoke_url = MagicMock(return_value='https://example.com/prod/test')
        
        # Call the method
        api_id, invoke_url = api_gateway_manager.create_or_update_api_gateway(
            'TestAPI', 'test', 'GET', lambda_function_name='test_function'
        )
        
        # Verify the result
        assert api_id == 'existing_api_id'
        assert invoke_url == 'https://example.com/prod/test'
        
        # Verify the mocks were called correctly
        api_gateway_manager.get_api_gateway_by_id.assert_called_once_with('existing_api_id')
        api_gateway_manager.find_resource_by_path.assert_called_once_with('existing_api_id', '/test')
        api_gateway_manager.create_resource.assert_called_once_with('existing_api_id', 'test')
        api_gateway_manager.create_method.assert_called_once_with('existing_api_id', 'new_resource_id', 'GET')
        api_gateway_manager.integrate_with_lambda.assert_called_once_with(
            'existing_api_id', 'new_resource_id', 'GET', 'test_function'
        )
        api_gateway_manager.add_lambda_permission.assert_called_once_with('test_function', 'existing_api_id')
        api_gateway_manager.deploy_api.assert_called_once_with('existing_api_id', 'prod')
        api_gateway_manager.get_invoke_url.assert_called_once_with('existing_api_id', 'prod', 'test')
        
    def test_create_or_update_api_gateway_with_existing_resource(self, api_gateway_manager):
        """Test create_or_update_api_gateway method with an existing resource."""
        # Configure the mocks
        api_id = "test_api_id"
        api_name = "test_api"
        resource_path = "test-resource"
        http_method = "GET"
        resource_id = "test_resource_id"
        new_resource_id = "new_resource_id"
        function_name = "test_function"
        invoke_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/{resource_path}"
        
        # Mock the config
        api_gateway_manager.config.api_gateway_id = api_id
        api_gateway_manager.config.lambda_function_name = function_name
        
        # Mock the API Gateway client responses
        api_gateway_manager.get_api_gateway_by_id = MagicMock(return_value={"id": api_id})
        api_gateway_manager.find_resource_by_path = MagicMock(return_value={"id": resource_id, "path": f"/{resource_path}"})
        api_gateway_manager.delete_method = MagicMock()
        api_gateway_manager.delete_resource = MagicMock()
        api_gateway_manager.create_resource = MagicMock(return_value=new_resource_id)
        api_gateway_manager.create_method = MagicMock()
        api_gateway_manager.integrate_with_lambda = MagicMock()
        api_gateway_manager.add_lambda_permission = MagicMock()
        api_gateway_manager.deploy_api = MagicMock()
        api_gateway_manager.get_invoke_url = MagicMock(return_value=invoke_url)
        
        # Call the method
        result_api_id, result_invoke_url = api_gateway_manager.create_or_update_api_gateway(
            api_name=api_name,
            resource_path=resource_path,
            http_method=http_method
        )
        
        # Verify the result
        assert result_api_id == api_id
        assert result_invoke_url == invoke_url
        
        # Verify the mocks were called correctly
        api_gateway_manager.get_api_gateway_by_id.assert_called_once_with(api_id)
        api_gateway_manager.find_resource_by_path.assert_called_once_with(api_id, f"/{resource_path}")
        api_gateway_manager.delete_method.assert_called_once_with(api_id, resource_id, http_method)
        api_gateway_manager.delete_resource.assert_called_once_with(api_id, resource_id)
        api_gateway_manager.create_resource.assert_called_once_with(api_id, resource_path)
        api_gateway_manager.create_method.assert_called_once_with(api_id, new_resource_id, http_method)
        api_gateway_manager.integrate_with_lambda.assert_called_once_with(api_id, new_resource_id, http_method, function_name)
        api_gateway_manager.add_lambda_permission.assert_called_once_with(function_name, api_id)
        api_gateway_manager.deploy_api.assert_called_once_with(api_id, 'prod')
        api_gateway_manager.get_invoke_url.assert_called_once_with(api_id, 'prod', resource_path)
