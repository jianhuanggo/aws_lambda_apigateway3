#!/usr/bin/env python3
"""
Example script to create an API Gateway endpoint integrated with a Lambda function.

This script demonstrates how to:
1. Create a new API Gateway
2. Create a resource and method
3. Integrate the method with a Lambda function
4. Deploy the API
5. Get the invoke URL
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api_gateway_lambda.api_gateway_manager import ApiGatewayManager
from src.api_gateway_lambda.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main function to create an API Gateway endpoint."""
    # Load environment variables
    load_dotenv()
    
    # Create an instance of the API Gateway Manager
    api_manager = ApiGatewayManager()
    
    try:
        # Create a new API Gateway or use an existing one
        api_name = "TestAPI"
        resource_path = "test-resource"
        http_method = "GET"
        
        logger.info(f"Creating or updating API Gateway '{api_name}' with resource '{resource_path}'")
        
        # Create or update the API Gateway
        api_id, invoke_url = api_manager.create_or_update_api_gateway(
            api_name=api_name,
            resource_path=resource_path,
            http_method=http_method
        )
        
        logger.info(f"API Gateway created/updated successfully with ID: {api_id}")
        logger.info(f"Invoke URL: {invoke_url}")
        
        # Print instructions for testing
        logger.info("\nTo test the API Gateway endpoint, run:")
        logger.info(f"curl -X {http_method} {invoke_url}")
        
    except Exception as e:
        logger.error(f"Error creating API Gateway: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
