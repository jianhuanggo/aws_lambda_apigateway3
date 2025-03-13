#!/usr/bin/env python3
"""
Complete example script demonstrating the full workflow:
1. Create an API Gateway
2. Integrate it with a Lambda function
3. Deploy the API
4. Call the API Gateway endpoint
5. Process the response

This script provides a comprehensive example of how to use the API Gateway Lambda integration package.
"""
import os
import sys
import json
import logging
import argparse
import time
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api_gateway_lambda.api_gateway_manager import ApiGatewayManager
from src.api_gateway_lambda.lambda_client import LambdaClient
from src.api_gateway_lambda.api_client import ApiClient
from src.api_gateway_lambda.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Complete API Gateway Lambda integration example')
    parser.add_argument('--api-name', type=str, default='CompleteExampleAPI', help='API Gateway name')
    parser.add_argument('--resource-path', type=str, default='complete-example', help='Resource path')
    parser.add_argument('--http-method', type=str, default='GET', help='HTTP method (GET, POST, etc.)')
    parser.add_argument('--stage', type=str, default='prod', help='API Gateway stage')
    parser.add_argument('--data', type=str, help='JSON data to send in the request body')
    parser.add_argument('--skip-create', action='store_true', help='Skip API Gateway creation')
    return parser.parse_args()


def main():
    """Main function for the complete example."""
    # Parse command line arguments
    args = parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Create instances of the managers and clients
    api_manager = ApiGatewayManager()
    lambda_client = LambdaClient()
    api_client = ApiClient()
    
    try:
        # Step 1: Create or update the API Gateway (if not skipped)
        if not args.skip_create:
            logger.info(f"Creating or updating API Gateway '{args.api_name}' with resource '{args.resource_path}'")
            
            api_id, invoke_url = api_manager.create_or_update_api_gateway(
                api_name=args.api_name,
                resource_path=args.resource_path,
                http_method=args.http_method
            )
            
            logger.info(f"API Gateway created/updated successfully with ID: {api_id}")
            logger.info(f"Invoke URL: {invoke_url}")
            
            # Wait for the API Gateway to be ready
            logger.info("Waiting for the API Gateway to be ready...")
            time.sleep(5)
        else:
            # Get the API Gateway ID from the config
            api_id = api_manager.config.api_gateway_id
            
            # Get the invoke URL
            invoke_url = api_manager.get_invoke_url(api_id, args.stage, args.resource_path)
            
            logger.info(f"Using existing API Gateway with ID: {api_id}")
            logger.info(f"Invoke URL: {invoke_url}")
        
        # Step 2: Parse the data if provided
        data = None
        if args.data:
            try:
                data = json.loads(args.data)
            except json.JSONDecodeError:
                logger.error("Invalid JSON data")
                sys.exit(1)
        else:
            # Use a default payload
            data = {
                "message": "Hello from the complete example!"
            }
        
        logger.info(f"Request data: {json.dumps(data, indent=2)}")
        
        # Step 3: Call the API Gateway endpoint
        logger.info(f"Calling API Gateway endpoint: {invoke_url}")
        logger.info(f"Method: {args.http_method}")
        
        response = api_client.make_request(
            url=invoke_url,
            method=args.http_method,
            data=data
        )
        
        logger.info("API Gateway endpoint called successfully")
        logger.info(f"Response: {json.dumps(response, indent=2)}")
        
        # Step 4: Also demonstrate direct Lambda invocation
        logger.info("\nDemonstrating direct Lambda invocation:")
        
        lambda_payload = {
            "queryStringParameters": {
                "source": "direct_invocation"
            },
            "body": json.dumps(data)
        }
        
        logger.info(f"Invoking Lambda function: {lambda_client.config.lambda_function_name}")
        logger.info(f"Payload: {json.dumps(lambda_payload, indent=2)}")
        
        lambda_response = lambda_client.invoke_lambda(payload=lambda_payload)
        
        logger.info("Lambda function invoked successfully")
        logger.info(f"Response: {json.dumps(lambda_response, indent=2)}")
        
        # Step 5: Compare the responses
        logger.info("\nComparing responses:")
        logger.info("API Gateway response and direct Lambda invocation should be similar")
        
    except Exception as e:
        logger.error(f"Error in complete example: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
