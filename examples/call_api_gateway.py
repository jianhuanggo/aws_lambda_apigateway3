#!/usr/bin/env python3
"""
Example script to call an API Gateway endpoint.

This script demonstrates how to:
1. Create an API client
2. Make a request to an API Gateway endpoint
3. Process the response
"""
import os
import sys
import json
import logging
import argparse
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api_gateway_lambda.api_client import ApiClient
from src.api_gateway_lambda.api_gateway_manager import ApiGatewayManager
from src.api_gateway_lambda.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Call an API Gateway endpoint')
    parser.add_argument('--method', type=str, default='GET', help='HTTP method (GET, POST, etc.)')
    parser.add_argument('--resource', type=str, default='test-resource', help='Resource path')
    parser.add_argument('--stage', type=str, default='prod', help='API Gateway stage')
    parser.add_argument('--data', type=str, help='JSON data to send in the request body')
    return parser.parse_args()


def main():
    """Main function to call an API Gateway endpoint."""
    # Parse command line arguments
    args = parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Create instances of the API Gateway Manager and API Client
    api_manager = ApiGatewayManager()
    api_client = ApiClient()
    
    try:
        # Get the API Gateway ID from the config
        api_id = api_manager.config.api_gateway_id
        
        # Get the invoke URL
        invoke_url = api_manager.get_invoke_url(api_id, args.stage, args.resource)
        
        logger.info(f"Calling API Gateway endpoint: {invoke_url}")
        logger.info(f"Method: {args.method}")
        
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
            method=args.method,
            data=data
        )
        
        logger.info("API Gateway endpoint called successfully")
        logger.info(f"Response: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error calling API Gateway endpoint: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
