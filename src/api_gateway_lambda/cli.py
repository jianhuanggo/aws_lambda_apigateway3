#!/usr/bin/env python3
"""
Command Line Interface for AWS Lambda API Gateway Integration.

This module provides a command-line interface to interact with AWS API Gateway and Lambda functions.
"""
import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional

from .api_gateway_manager import ApiGatewayManager
from .lambda_client import LambdaClient
from .api_client import ApiClient
from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_api_gateway(args: argparse.Namespace) -> None:
    """
    Create or update an API Gateway endpoint.

    Args:
        args: Command line arguments.
    """
    api_manager = ApiGatewayManager(profile_name=args.profile)
    
    try:
        api_id, invoke_url = api_manager.create_or_update_api_gateway(
            api_name=args.api_name,
            resource_path=args.resource_path,
            http_method=args.http_method,
            stage_name=args.stage,
            lambda_function_name=args.function_name
        )
        
        logger.info(f"API Gateway created/updated successfully with ID: {api_id}")
        logger.info(f"Invoke URL: {invoke_url}")
        
        # Print instructions for testing
        logger.info("\nTo test the API Gateway endpoint, run:")
        logger.info(f"curl -X {args.http_method} {invoke_url}")
        
    except Exception as e:
        logger.error(f"Error creating API Gateway: {e}")
        sys.exit(1)


def invoke_lambda(args: argparse.Namespace) -> None:
    """
    Invoke a Lambda function directly.

    Args:
        args: Command line arguments.
    """
    lambda_client = LambdaClient(profile_name=args.profile)
    
    try:
        # Parse the payload if provided
        payload = {}
        if args.payload:
            try:
                payload = json.loads(args.payload)
            except json.JSONDecodeError:
                logger.error("Invalid JSON payload")
                sys.exit(1)
        
        logger.info(f"Invoking Lambda function: {args.function_name or lambda_client.config.lambda_function_name}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Invoke the Lambda function
        response = lambda_client.invoke_lambda(
            function_name=args.function_name,
            payload=payload
        )
        
        logger.info("Lambda function invoked successfully")
        logger.info(f"Response: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error invoking Lambda function: {e}")
        sys.exit(1)


def call_api(args: argparse.Namespace) -> None:
    """
    Call an API Gateway endpoint.

    Args:
        args: Command line arguments.
    """
    api_client = ApiClient(profile_name=args.profile)
    api_manager = ApiGatewayManager(profile_name=args.profile)
    
    try:
        # Get the API Gateway ID from the config if not provided
        api_id = args.api_id or api_manager.config.api_gateway_id
        
        # Get the invoke URL
        invoke_url = api_manager.get_invoke_url(api_id, args.stage, args.resource_path)
        
        logger.info(f"Calling API Gateway endpoint: {invoke_url}")
        logger.info(f"Method: {args.http_method}")
        
        # Parse the data if provided
        data = None
        if args.data:
            try:
                data = json.loads(args.data)
                logger.info(f"Data: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                logger.error("Invalid JSON data")
                sys.exit(1)
        
        # Make the request
        response = api_client.make_request(
            url=invoke_url,
            method=args.http_method,
            data=data
        )
        
        logger.info("API Gateway endpoint called successfully")
        logger.info(f"Response: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error calling API Gateway endpoint: {e}")
        sys.exit(1)


def list_resources(args: argparse.Namespace) -> None:
    """
    List resources for an API Gateway.

    Args:
        args: Command line arguments.
    """
    api_manager = ApiGatewayManager(profile_name=args.profile)
    
    try:
        # Get the API Gateway ID from the config if not provided
        api_id = args.api_id or api_manager.config.api_gateway_id
        
        # Get the resources
        resources = api_manager.get_resources(api_id)
        
        logger.info(f"Resources for API Gateway {api_id}:")
        for resource in resources:
            logger.info(f"  ID: {resource.get('id')}")
            logger.info(f"  Path: {resource.get('path')}")
            logger.info(f"  Resource Methods: {', '.join(resource.get('resourceMethods', {}).keys()) or 'None'}")
            logger.info("")
        
    except Exception as e:
        logger.error(f"Error listing resources: {e}")
        sys.exit(1)


def delete_resource(args: argparse.Namespace) -> None:
    """
    Delete a resource from an API Gateway.

    Args:
        args: Command line arguments.
    """
    api_manager = ApiGatewayManager(profile_name=args.profile)
    
    try:
        # Get the API Gateway ID from the config if not provided
        api_id = args.api_id or api_manager.config.api_gateway_id
        
        # Find the resource by path if resource_id is not provided
        resource_id = args.resource_id
        if not resource_id and args.resource_path:
            resource = api_manager.find_resource_by_path(api_id, args.resource_path)
            if resource:
                resource_id = resource['id']
            else:
                logger.error(f"Resource with path '{args.resource_path}' not found")
                sys.exit(1)
        
        # Delete the resource
        api_manager.delete_resource(api_id, resource_id)
        
        logger.info(f"Resource {resource_id} deleted successfully")
        
    except Exception as e:
        logger.error(f"Error deleting resource: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='AWS Lambda API Gateway Integration CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create API Gateway command
    create_parser = subparsers.add_parser('create-api', help='Create or update an API Gateway endpoint')
    create_parser.add_argument('--api-name', type=str, required=True, help='API Gateway name')
    create_parser.add_argument('--resource-path', type=str, required=True, help='Resource path')
    create_parser.add_argument('--http-method', type=str, default='GET', help='HTTP method (GET, POST, etc.)')
    create_parser.add_argument('--stage', type=str, default='prod', help='API Gateway stage')
    create_parser.add_argument('--function-name', type=str, help='Lambda function name (defaults to config)')
    create_parser.add_argument('--profile', type=str, default='latest', help='AWS profile name to use')
    
    # Invoke Lambda command
    invoke_parser = subparsers.add_parser('invoke-lambda', help='Invoke a Lambda function directly')
    invoke_parser.add_argument('--function-name', type=str, help='Lambda function name (defaults to config)')
    invoke_parser.add_argument('--payload', type=str, help='JSON payload to send to the Lambda function')
    invoke_parser.add_argument('--profile', type=str, default='latest', help='AWS profile name to use')
    
    # Call API command
    call_parser = subparsers.add_parser('call-api', help='Call an API Gateway endpoint')
    call_parser.add_argument('--api-id', type=str, help='API Gateway ID (defaults to config)')
    call_parser.add_argument('--resource-path', type=str, required=True, help='Resource path')
    call_parser.add_argument('--http-method', type=str, default='GET', help='HTTP method (GET, POST, etc.)')
    call_parser.add_argument('--stage', type=str, default='prod', help='API Gateway stage')
    call_parser.add_argument('--data', type=str, help='JSON data to send in the request body')
    call_parser.add_argument('--profile', type=str, default='latest', help='AWS profile name to use')
    
    # List resources command
    list_parser = subparsers.add_parser('list-resources', help='List resources for an API Gateway')
    list_parser.add_argument('--api-id', type=str, help='API Gateway ID (defaults to config)')
    list_parser.add_argument('--profile', type=str, default='latest', help='AWS profile name to use')
    
    # Delete resource command
    delete_parser = subparsers.add_parser('delete-resource', help='Delete a resource from an API Gateway')
    delete_parser.add_argument('--api-id', type=str, help='API Gateway ID (defaults to config)')
    delete_parser.add_argument('--resource-id', type=str, help='Resource ID to delete')
    delete_parser.add_argument('--resource-path', type=str, help='Resource path to delete (alternative to resource-id)')
    delete_parser.add_argument('--profile', type=str, default='latest', help='AWS profile name to use')
    
    args = parser.parse_args()
    
    if args.command == 'create-api':
        create_api_gateway(args)
    elif args.command == 'invoke-lambda':
        invoke_lambda(args)
    elif args.command == 'call-api':
        call_api(args)
    elif args.command == 'list-resources':
        list_resources(args)
    elif args.command == 'delete-resource':
        delete_resource(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
