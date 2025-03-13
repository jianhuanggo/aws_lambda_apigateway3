#!/usr/bin/env python3
"""
Example script to invoke a Lambda function directly.

This script demonstrates how to:
1. Create a Lambda client
2. Invoke a Lambda function with a payload
3. Process the response
"""
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api_gateway_lambda.lambda_client import LambdaClient
from src.api_gateway_lambda.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main function to invoke a Lambda function."""
    # Load environment variables
    load_dotenv()
    
    # Create an instance of the Lambda Client
    lambda_client = LambdaClient()
    
    try:
        # Define the payload to send to the Lambda function
        payload = {
            "queryStringParameters": {
                "param1": "value1",
                "param2": "value2"
            },
            "body": json.dumps({
                "message": "Hello from Lambda!"
            })
        }
        
        logger.info(f"Invoking Lambda function: {lambda_client.config.lambda_function_name}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Invoke the Lambda function
        response = lambda_client.invoke_lambda(payload=payload)
        
        logger.info("Lambda function invoked successfully")
        logger.info(f"Response: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error invoking Lambda function: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
