"""Tests for the CLI module."""
import json
import pytest
import argparse
from unittest.mock import patch, MagicMock, call

from src.api_gateway_lambda.cli import (
    main, create_api_gateway, invoke_lambda, call_api, list_resources, delete_resource
)


class TestCLI:
    """Test cases for the CLI module."""

    @pytest.fixture
    def mock_api_gateway_manager(self):
        """Fixture for mocking ApiGatewayManager."""
        with patch('src.api_gateway_lambda.cli.ApiGatewayManager') as mock:
            yield mock

    @pytest.fixture
    def mock_lambda_client(self):
        """Fixture for mocking LambdaClient."""
        with patch('src.api_gateway_lambda.cli.LambdaClient') as mock:
            yield mock

    @pytest.fixture
    def mock_api_client(self):
        """Fixture for mocking ApiClient."""
        with patch('src.api_gateway_lambda.cli.ApiClient') as mock:
            yield mock

    @pytest.fixture
    def mock_argparse(self):
        """Fixture for mocking argparse."""
        with patch('src.api_gateway_lambda.cli.argparse.ArgumentParser') as mock:
            yield mock

    @pytest.fixture
    def mock_sys_exit(self):
        """Fixture for mocking sys.exit."""
        with patch('src.api_gateway_lambda.cli.sys.exit') as mock:
            yield mock

    def test_create_api_gateway(self, mock_api_gateway_manager):
        """Test create_api_gateway function."""
        # Configure the mock
        mock_manager_instance = mock_api_gateway_manager.return_value
        mock_manager_instance.create_or_update_api_gateway.return_value = ('test_api_id', 'https://test-url.com')
        
        # Create args
        args = argparse.Namespace(
            api_name='test_api',
            resource_path='test-resource',
            http_method='GET',
            stage='prod',
            function_name='test_function',
            profile='latest'
        )
        
        # Call the function
        create_api_gateway(args)
        
        # Verify the mock was called correctly
        mock_manager_instance.create_or_update_api_gateway.assert_called_once_with(
            api_name='test_api',
            resource_path='test-resource',
            http_method='GET',
            stage_name='prod',
            lambda_function_name='test_function'
        )

    def test_create_api_gateway_error(self, mock_api_gateway_manager, mock_sys_exit):
        """Test create_api_gateway function with error."""
        # Configure the mock to raise an exception
        mock_manager_instance = mock_api_gateway_manager.return_value
        mock_manager_instance.create_or_update_api_gateway.side_effect = Exception('Test error')
        
        # Create args
        args = argparse.Namespace(
            api_name='test_api',
            resource_path='test-resource',
            http_method='GET',
            stage='prod',
            function_name='test_function',
            profile='latest'
        )
        
        # Call the function
        create_api_gateway(args)
        
        # Verify sys.exit was called
        mock_sys_exit.assert_called_once_with(1)

    def test_invoke_lambda(self, mock_lambda_client):
        """Test invoke_lambda function."""
        # Configure the mock
        mock_client_instance = mock_lambda_client.return_value
        mock_client_instance.invoke_lambda.return_value = {'result': 'success'}
        mock_client_instance.config.lambda_function_name = 'default_function'
        
        # Create args
        args = argparse.Namespace(
            function_name='test_function',
            payload='{"key": "value"}',
            profile='latest'
        )
        
        # Call the function
        invoke_lambda(args)
        
        # Verify the mock was called correctly
        mock_client_instance.invoke_lambda.assert_called_once_with(
            function_name='test_function',
            payload={'key': 'value'}
        )

    def test_invoke_lambda_with_default_function(self, mock_lambda_client):
        """Test invoke_lambda function with default function name."""
        # Configure the mock
        mock_client_instance = mock_lambda_client.return_value
        mock_client_instance.invoke_lambda.return_value = {'result': 'success'}
        mock_client_instance.config.lambda_function_name = 'default_function'
        
        # Create args
        args = argparse.Namespace(
            function_name=None,
            payload='{"key": "value"}',
            profile='latest'
        )
        
        # Call the function
        invoke_lambda(args)
        
        # Verify the mock was called correctly
        mock_client_instance.invoke_lambda.assert_called_once_with(
            function_name=None,
            payload={'key': 'value'}
        )

    def test_invoke_lambda_with_invalid_payload(self, mock_lambda_client, mock_sys_exit):
        """Test invoke_lambda function with invalid payload."""
        # Configure the mock
        mock_client_instance = mock_lambda_client.return_value
        
        # Create args with invalid JSON
        args = argparse.Namespace(
            function_name='test_function',
            payload='invalid_json',
            profile='latest'
        )
        
        # Call the function
        invoke_lambda(args)
        
        # Verify sys.exit was called (we don't check the number of calls because
        # it might be called multiple times due to error handling)
        mock_sys_exit.assert_called_with(1)

    def test_call_api(self, mock_api_client, mock_api_gateway_manager):
        """Test call_api function."""
        # Configure the mocks
        mock_client_instance = mock_api_client.return_value
        mock_client_instance.make_request.return_value = {'result': 'success'}
        
        mock_manager_instance = mock_api_gateway_manager.return_value
        mock_manager_instance.get_invoke_url.return_value = 'https://test-url.com'
        mock_manager_instance.config.api_gateway_id = 'default_api_id'
        
        # Create args
        args = argparse.Namespace(
            api_id='test_api_id',
            resource_path='test-resource',
            http_method='GET',
            stage='prod',
            data='{"key": "value"}',
            profile='latest'
        )
        
        # Call the function
        call_api(args)
        
        # Verify the mocks were called correctly
        mock_manager_instance.get_invoke_url.assert_called_once_with('test_api_id', 'prod', 'test-resource')
        mock_client_instance.make_request.assert_called_once_with(
            url='https://test-url.com',
            method='GET',
            data={'key': 'value'}
        )

    def test_call_api_with_default_api_id(self, mock_api_client, mock_api_gateway_manager):
        """Test call_api function with default API ID."""
        # Configure the mocks
        mock_client_instance = mock_api_client.return_value
        mock_client_instance.make_request.return_value = {'result': 'success'}
        
        mock_manager_instance = mock_api_gateway_manager.return_value
        mock_manager_instance.get_invoke_url.return_value = 'https://test-url.com'
        mock_manager_instance.config.api_gateway_id = 'default_api_id'
        
        # Create args
        args = argparse.Namespace(
            api_id=None,
            resource_path='test-resource',
            http_method='GET',
            stage='prod',
            data=None,
            profile='latest'
        )
        
        # Call the function
        call_api(args)
        
        # Verify the mocks were called correctly
        mock_manager_instance.get_invoke_url.assert_called_once_with('default_api_id', 'prod', 'test-resource')
        mock_client_instance.make_request.assert_called_once_with(
            url='https://test-url.com',
            method='GET',
            data=None
        )

    def test_list_resources(self, mock_api_gateway_manager):
        """Test list_resources function."""
        # Configure the mock
        mock_manager_instance = mock_api_gateway_manager.return_value
        mock_manager_instance.get_resources.return_value = [
            {
                'id': 'resource1',
                'path': '/test',
                'resourceMethods': {'GET': {}}
            },
            {
                'id': 'resource2',
                'path': '/test/sub',
                'resourceMethods': {}
            }
        ]
        mock_manager_instance.config.api_gateway_id = 'default_api_id'
        
        # Create args
        args = argparse.Namespace(
            api_id='test_api_id',
            profile='latest'
        )
        
        # Call the function
        list_resources(args)
        
        # Verify the mock was called correctly
        mock_manager_instance.get_resources.assert_called_once_with('test_api_id')

    def test_delete_resource(self, mock_api_gateway_manager):
        """Test delete_resource function."""
        # Configure the mock
        mock_manager_instance = mock_api_gateway_manager.return_value
        mock_manager_instance.config.api_gateway_id = 'default_api_id'
        
        # Create args
        args = argparse.Namespace(
            api_id='test_api_id',
            resource_id='test_resource_id',
            resource_path=None,
            profile='latest'
        )
        
        # Call the function
        delete_resource(args)
        
        # Verify the mock was called correctly
        mock_manager_instance.delete_resource.assert_called_once_with('test_api_id', 'test_resource_id')

    def test_delete_resource_by_path(self, mock_api_gateway_manager):
        """Test delete_resource function using resource path."""
        # Configure the mock
        mock_manager_instance = mock_api_gateway_manager.return_value
        mock_manager_instance.config.api_gateway_id = 'default_api_id'
        mock_manager_instance.find_resource_by_path.return_value = {'id': 'found_resource_id'}
        
        # Create args
        args = argparse.Namespace(
            api_id='test_api_id',
            resource_id=None,
            resource_path='/test-resource',
            profile='latest'
        )
        
        # Call the function
        delete_resource(args)
        
        # Verify the mocks were called correctly
        mock_manager_instance.find_resource_by_path.assert_called_once_with('test_api_id', '/test-resource')
        mock_manager_instance.delete_resource.assert_called_once_with('test_api_id', 'found_resource_id')

    def test_delete_resource_by_path_not_found(self, mock_api_gateway_manager, mock_sys_exit):
        """Test delete_resource function with resource path not found."""
        # Configure the mock
        mock_manager_instance = mock_api_gateway_manager.return_value
        mock_manager_instance.config.api_gateway_id = 'default_api_id'
        mock_manager_instance.find_resource_by_path.return_value = None
        
        # Create args
        args = argparse.Namespace(
            api_id='test_api_id',
            resource_id=None,
            resource_path='/test-resource',
            profile='latest'
        )
        
        # Call the function
        delete_resource(args)
        
        # Verify sys.exit was called
        mock_sys_exit.assert_called_once_with(1)

    @patch('src.api_gateway_lambda.cli.argparse.ArgumentParser')
    @patch('src.api_gateway_lambda.cli.create_api_gateway')
    def test_main_create_api(self, mock_create_api, mock_parser):
        """Test main function with create-api command."""
        # Configure the mock parser
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.parse_args.return_value = argparse.Namespace(
            command='create-api',
            api_name='test_api',
            resource_path='test-resource',
            http_method='GET',
            stage='prod',
            function_name='test_function'
        )
        
        # Call the function
        main()
        
        # Verify the mock was called correctly
        mock_create_api.assert_called_once()

    @patch('src.api_gateway_lambda.cli.argparse.ArgumentParser')
    @patch('src.api_gateway_lambda.cli.invoke_lambda')
    def test_main_invoke_lambda(self, mock_invoke, mock_parser):
        """Test main function with invoke-lambda command."""
        # Configure the mock parser
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.parse_args.return_value = argparse.Namespace(
            command='invoke-lambda',
            function_name='test_function',
            payload='{"key": "value"}'
        )
        
        # Call the function
        main()
        
        # Verify the mock was called correctly
        mock_invoke.assert_called_once()

    @patch('src.api_gateway_lambda.cli.argparse.ArgumentParser')
    @patch('src.api_gateway_lambda.cli.call_api')
    def test_main_call_api(self, mock_call_api, mock_parser):
        """Test main function with call-api command."""
        # Configure the mock parser
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.parse_args.return_value = argparse.Namespace(
            command='call-api',
            api_id='test_api_id',
            resource_path='test-resource',
            http_method='GET',
            stage='prod',
            data='{"key": "value"}'
        )
        
        # Call the function
        main()
        
        # Verify the mock was called correctly
        mock_call_api.assert_called_once()

    @patch('src.api_gateway_lambda.cli.argparse.ArgumentParser')
    @patch('src.api_gateway_lambda.cli.list_resources')
    def test_main_list_resources(self, mock_list, mock_parser):
        """Test main function with list-resources command."""
        # Configure the mock parser
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.parse_args.return_value = argparse.Namespace(
            command='list-resources',
            api_id='test_api_id'
        )
        
        # Call the function
        main()
        
        # Verify the mock was called correctly
        mock_list.assert_called_once()

    @patch('src.api_gateway_lambda.cli.argparse.ArgumentParser')
    @patch('src.api_gateway_lambda.cli.delete_resource')
    def test_main_delete_resource(self, mock_delete, mock_parser):
        """Test main function with delete-resource command."""
        # Configure the mock parser
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.parse_args.return_value = argparse.Namespace(
            command='delete-resource',
            api_id='test_api_id',
            resource_id='test_resource_id',
            resource_path=None
        )
        
        # Call the function
        main()
        
        # Verify the mock was called correctly
        mock_delete.assert_called_once()

    @patch('src.api_gateway_lambda.cli.argparse.ArgumentParser')
    @patch('src.api_gateway_lambda.cli.sys.exit')
    def test_main_no_command(self, mock_exit, mock_parser):
        """Test main function with no command."""
        # Configure the mock parser
        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.parse_args.return_value = argparse.Namespace(
            command=None
        )
        
        # Call the function
        main()
        
        # Verify the mock was called correctly
        mock_parser_instance.print_help.assert_called_once()
        mock_exit.assert_called_once_with(1)
