#!/usr/bin/env python3
"""
Advanced example script showcasing various features of the AWS Lambda API Gateway integration.

This script demonstrates:
1. Creating multiple resources in an API Gateway
2. Setting up different HTTP methods (GET, POST, PUT, DELETE)
3. Passing different types of payloads to the Lambda function
4. Error handling and retries
5. Parameterized requests
6. Batch processing
"""
import os
import sys
import json
import time
import logging
import argparse
import concurrent.futures
from typing import Dict, Any, List, Optional
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


class AdvancedExample:
    """Advanced example class demonstrating various features."""

    def __init__(self):
        """Initialize the example with API Gateway and Lambda clients."""
        # Load environment variables
        load_dotenv()
        
        # Create instances of the managers and clients
        self.api_manager = ApiGatewayManager()
        self.lambda_client = LambdaClient()
        self.api_client = ApiClient()
        
        # Get the API Gateway ID from the config
        self.api_id = self.api_manager.config.api_gateway_id
        self.lambda_function = self.api_manager.config.lambda_function_name
        
        # Define the base resource path
        self.base_resource_path = "advanced-example"
        
        # Define the stage name
        self.stage_name = "prod"

    def setup_api_gateway(self) -> Dict[str, str]:
        """
        Set up the API Gateway with multiple resources and methods.
        
        Returns:
            Dict[str, str]: Dictionary mapping resource paths to their IDs
        """
        logger.info(f"Setting up API Gateway with ID: {self.api_id}")
        
        # Create the base resource
        try:
            base_resource = self.api_manager.find_resource_by_path(self.api_id, f"/{self.base_resource_path}")
            if base_resource:
                base_resource_id = base_resource['id']
                logger.info(f"Using existing base resource: {self.base_resource_path}")
            else:
                base_resource_id = self.api_manager.create_resource(self.api_id, self.base_resource_path)
                logger.info(f"Created base resource: {self.base_resource_path}")
        except Exception as e:
            logger.error(f"Error creating base resource: {e}")
            raise
        
        # Define sub-resources to create
        sub_resources = ["items", "users", "metadata", "batch"]
        resource_ids = {self.base_resource_path: base_resource_id}
        
        # Create sub-resources
        for resource_path in sub_resources:
            try:
                # Check if the resource already exists
                full_path = f"/{self.base_resource_path}/{resource_path}"
                existing_resource = self.api_manager.find_resource_by_path(self.api_id, full_path)
                
                if existing_resource:
                    resource_id = existing_resource['id']
                    logger.info(f"Using existing resource: {resource_path}")
                else:
                    # Create the resource
                    resource_id = self.api_manager.create_resource(
                        self.api_id, resource_path, base_resource_id
                    )
                    logger.info(f"Created resource: {resource_path}")
                
                resource_ids[resource_path] = resource_id
                
                # Set up methods for the resource
                self._setup_methods_for_resource(resource_path, resource_id)
                
            except Exception as e:
                logger.error(f"Error creating resource {resource_path}: {e}")
                continue
        
        # Deploy the API
        self.api_manager.deploy_api(self.api_id, self.stage_name)
        logger.info(f"Deployed API Gateway to stage: {self.stage_name}")
        
        return resource_ids

    def _setup_methods_for_resource(self, resource_path: str, resource_id: str) -> None:
        """
        Set up HTTP methods for a resource.
        
        Args:
            resource_path (str): The path of the resource
            resource_id (str): The ID of the resource
        """
        # Define methods to create based on the resource
        if resource_path == "items":
            methods = ["GET", "POST", "PUT", "DELETE"]
        elif resource_path == "users":
            methods = ["GET", "POST"]
        elif resource_path == "metadata":
            methods = ["GET"]
        elif resource_path == "batch":
            methods = ["POST"]
        else:
            methods = ["GET"]
        
        # Create methods for the resource
        for method in methods:
            try:
                # Create the method
                try:
                    self.api_manager.create_method(self.api_id, resource_id, method)
                    logger.info(f"Created {method} method for resource {resource_path}")
                except Exception as e:
                    if "ConflictException" in str(e):
                        logger.warning(f"Method {method} already exists for resource {resource_path}")
                    else:
                        raise
                
                # Integrate with Lambda
                self.api_manager.integrate_with_lambda(
                    self.api_id, resource_id, method, self.lambda_function
                )
                logger.info(f"Integrated {method} method with Lambda function for resource {resource_path}")
                
            except Exception as e:
                logger.error(f"Error setting up {method} method for resource {resource_path}: {e}")
                continue

    def get_invoke_urls(self, resource_ids: Dict[str, str]) -> Dict[str, str]:
        """
        Get the invoke URLs for all resources.
        
        Args:
            resource_ids (Dict[str, str]): Dictionary mapping resource paths to their IDs
            
        Returns:
            Dict[str, str]: Dictionary mapping resource paths to their invoke URLs
        """
        invoke_urls = {}
        
        for resource_path, _ in resource_ids.items():
            if resource_path == self.base_resource_path:
                path = resource_path
            else:
                path = f"{self.base_resource_path}/{resource_path}"
            
            invoke_url = self.api_manager.get_invoke_url(self.api_id, self.stage_name, path)
            invoke_urls[resource_path] = invoke_url
            
            logger.info(f"Invoke URL for {resource_path}: {invoke_url}")
        
        return invoke_urls

    def demonstrate_get_requests(self, invoke_urls: Dict[str, str]) -> None:
        """
        Demonstrate GET requests to different resources.
        
        Args:
            invoke_urls (Dict[str, str]): Dictionary mapping resource paths to their invoke URLs
        """
        logger.info("\n=== Demonstrating GET Requests ===")
        
        # GET request to items resource
        if "items" in invoke_urls:
            try:
                logger.info("Making GET request to items resource")
                response = self.api_client.make_request(
                    url=invoke_urls["items"],
                    method="GET",
                    params={"limit": 10, "offset": 0}
                )
                logger.info(f"Response from items: {json.dumps(response, indent=2)}")
            except Exception as e:
                logger.error(f"Error making GET request to items: {e}")
        
        # GET request to users resource
        if "users" in invoke_urls:
            try:
                logger.info("Making GET request to users resource")
                response = self.api_client.make_request(
                    url=invoke_urls["users"],
                    method="GET",
                    params={"role": "admin"}
                )
                logger.info(f"Response from users: {json.dumps(response, indent=2)}")
            except Exception as e:
                logger.error(f"Error making GET request to users: {e}")
        
        # GET request to metadata resource
        if "metadata" in invoke_urls:
            try:
                logger.info("Making GET request to metadata resource")
                response = self.api_client.make_request(
                    url=invoke_urls["metadata"],
                    method="GET"
                )
                logger.info(f"Response from metadata: {json.dumps(response, indent=2)}")
            except Exception as e:
                logger.error(f"Error making GET request to metadata: {e}")

    def demonstrate_post_requests(self, invoke_urls: Dict[str, str]) -> None:
        """
        Demonstrate POST requests to different resources.
        
        Args:
            invoke_urls (Dict[str, str]): Dictionary mapping resource paths to their invoke URLs
        """
        logger.info("\n=== Demonstrating POST Requests ===")
        
        # POST request to items resource
        if "items" in invoke_urls:
            try:
                logger.info("Making POST request to items resource")
                item_data = {
                    "name": "Test Item",
                    "description": "This is a test item",
                    "price": 19.99,
                    "quantity": 100
                }
                response = self.api_client.make_request(
                    url=invoke_urls["items"],
                    method="POST",
                    data=item_data
                )
                logger.info(f"Response from items POST: {json.dumps(response, indent=2)}")
            except Exception as e:
                logger.error(f"Error making POST request to items: {e}")
        
        # POST request to users resource
        if "users" in invoke_urls:
            try:
                logger.info("Making POST request to users resource")
                user_data = {
                    "username": "testuser",
                    "email": "test@example.com",
                    "role": "user"
                }
                response = self.api_client.make_request(
                    url=invoke_urls["users"],
                    method="POST",
                    data=user_data
                )
                logger.info(f"Response from users POST: {json.dumps(response, indent=2)}")
            except Exception as e:
                logger.error(f"Error making POST request to users: {e}")

    def demonstrate_put_requests(self, invoke_urls: Dict[str, str]) -> None:
        """
        Demonstrate PUT requests to different resources.
        
        Args:
            invoke_urls (Dict[str, str]): Dictionary mapping resource paths to their invoke URLs
        """
        logger.info("\n=== Demonstrating PUT Requests ===")
        
        # PUT request to items resource
        if "items" in invoke_urls:
            try:
                logger.info("Making PUT request to items resource")
                item_data = {
                    "id": "item-123",
                    "name": "Updated Test Item",
                    "description": "This is an updated test item",
                    "price": 29.99,
                    "quantity": 50
                }
                response = self.api_client.make_request(
                    url=invoke_urls["items"],
                    method="PUT",
                    data=item_data
                )
                logger.info(f"Response from items PUT: {json.dumps(response, indent=2)}")
            except Exception as e:
                logger.error(f"Error making PUT request to items: {e}")

    def demonstrate_delete_requests(self, invoke_urls: Dict[str, str]) -> None:
        """
        Demonstrate DELETE requests to different resources.
        
        Args:
            invoke_urls (Dict[str, str]): Dictionary mapping resource paths to their invoke URLs
        """
        logger.info("\n=== Demonstrating DELETE Requests ===")
        
        # DELETE request to items resource
        if "items" in invoke_urls:
            try:
                logger.info("Making DELETE request to items resource")
                response = self.api_client.make_request(
                    url=f"{invoke_urls['items']}?id=item-123",
                    method="DELETE"
                )
                logger.info(f"Response from items DELETE: {json.dumps(response, indent=2)}")
            except Exception as e:
                logger.error(f"Error making DELETE request to items: {e}")

    def demonstrate_batch_processing(self, invoke_urls: Dict[str, str]) -> None:
        """
        Demonstrate batch processing with concurrent requests.
        
        Args:
            invoke_urls (Dict[str, str]): Dictionary mapping resource paths to their invoke URLs
        """
        logger.info("\n=== Demonstrating Batch Processing ===")
        
        if "batch" in invoke_urls:
            try:
                # Create batch data
                batch_items = [
                    {"id": f"item-{i}", "name": f"Batch Item {i}", "operation": "create"}
                    for i in range(1, 6)
                ]
                
                logger.info(f"Processing batch of {len(batch_items)} items")
                
                # Send batch request
                response = self.api_client.make_request(
                    url=invoke_urls["batch"],
                    method="POST",
                    data={"items": batch_items}
                )
                
                logger.info(f"Batch processing response: {json.dumps(response, indent=2)}")
                
            except Exception as e:
                logger.error(f"Error in batch processing: {e}")

    def demonstrate_error_handling_and_retries(self, invoke_urls: Dict[str, str]) -> None:
        """
        Demonstrate error handling and retries.
        
        Args:
            invoke_urls (Dict[str, str]): Dictionary mapping resource paths to their invoke URLs
        """
        logger.info("\n=== Demonstrating Error Handling and Retries ===")
        
        if "items" in invoke_urls:
            # Simulate a request that will fail
            try:
                logger.info("Making request that will fail (invalid data)")
                invalid_data = {"invalid_field": "This will cause an error"}
                
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        response = self.api_client.make_request(
                            url=invoke_urls["items"],
                            method="POST",
                            data=invalid_data,
                            timeout=5  # Short timeout
                        )
                        logger.info(f"Response: {json.dumps(response, indent=2)}")
                        break
                    except Exception as e:
                        retry_count += 1
                        logger.warning(f"Request failed (attempt {retry_count}/{max_retries}): {e}")
                        
                        if retry_count < max_retries:
                            # Exponential backoff
                            wait_time = 2 ** retry_count
                            logger.info(f"Retrying in {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            logger.error("Max retries reached. Giving up.")
            except Exception as e:
                logger.error(f"Error in error handling demonstration: {e}")

    def demonstrate_direct_lambda_invocation(self) -> None:
        """Demonstrate direct Lambda invocation with different payloads."""
        logger.info("\n=== Demonstrating Direct Lambda Invocation ===")
        
        try:
            # Invoke Lambda with different payloads
            payloads = [
                {"action": "get_metadata", "parameters": {}},
                {"action": "get_items", "parameters": {"limit": 5}},
                {"action": "create_item", "parameters": {"name": "Direct Lambda Item"}}
            ]
            
            for i, payload in enumerate(payloads):
                logger.info(f"Invoking Lambda directly with payload {i+1}")
                logger.info(f"Payload: {json.dumps(payload, indent=2)}")
                
                response = self.lambda_client.invoke_lambda(payload=payload)
                logger.info(f"Response from Lambda: {json.dumps(response, indent=2)}")
                
                # Add a small delay between invocations
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in direct Lambda invocation: {e}")

    def demonstrate_parallel_requests(self, invoke_urls: Dict[str, str]) -> None:
        """
        Demonstrate parallel requests to the API Gateway.
        
        Args:
            invoke_urls (Dict[str, str]): Dictionary mapping resource paths to their invoke URLs
        """
        logger.info("\n=== Demonstrating Parallel Requests ===")
        
        if "items" not in invoke_urls:
            logger.warning("Items resource not available for parallel requests demonstration")
            return
        
        # Define requests to make in parallel
        requests = [
            {"url": invoke_urls["items"], "method": "GET", "params": {"id": f"item-{i}"}}
            for i in range(1, 6)
        ]
        
        logger.info(f"Making {len(requests)} parallel requests")
        
        # Use ThreadPoolExecutor to make parallel requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            # Submit all requests
            for req in requests:
                future = executor.submit(
                    self.api_client.make_request,
                    url=req["url"],
                    method=req["method"],
                    params=req.get("params"),
                    data=req.get("data")
                )
                futures.append(future)
            
            # Process results as they complete
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                try:
                    result = future.result()
                    logger.info(f"Result from parallel request {i+1}: {json.dumps(result, indent=2)}")
                except Exception as e:
                    logger.error(f"Error in parallel request {i+1}: {e}")

    def run_all_demonstrations(self) -> None:
        """Run all demonstrations."""
        try:
            # Set up the API Gateway
            resource_ids = self.setup_api_gateway()
            
            # Get the invoke URLs
            invoke_urls = self.get_invoke_urls(resource_ids)
            
            # Run all demonstrations
            self.demonstrate_get_requests(invoke_urls)
            self.demonstrate_post_requests(invoke_urls)
            self.demonstrate_put_requests(invoke_urls)
            self.demonstrate_delete_requests(invoke_urls)
            self.demonstrate_batch_processing(invoke_urls)
            self.demonstrate_error_handling_and_retries(invoke_urls)
            self.demonstrate_direct_lambda_invocation()
            self.demonstrate_parallel_requests(invoke_urls)
            
            logger.info("\n=== All demonstrations completed successfully ===")
            
        except Exception as e:
            logger.error(f"Error running demonstrations: {e}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Advanced API Gateway Lambda integration example')
    parser.add_argument('--setup-only', action='store_true', help='Only set up the API Gateway without running demonstrations')
    parser.add_argument('--demo', type=str, choices=['get', 'post', 'put', 'delete', 'batch', 'error', 'lambda', 'parallel', 'all'], 
                        default='all', help='Specific demonstration to run')
    return parser.parse_args()


def main():
    """Main function for the advanced example."""
    # Parse command line arguments
    args = parse_args()
    
    # Create the advanced example
    example = AdvancedExample()
    
    try:
        # Set up the API Gateway
        resource_ids = example.setup_api_gateway()
        
        # Get the invoke URLs
        invoke_urls = example.get_invoke_urls(resource_ids)
        
        # Run the specified demonstration or all of them
        if args.setup_only:
            logger.info("API Gateway setup completed. Skipping demonstrations.")
        elif args.demo == 'get':
            example.demonstrate_get_requests(invoke_urls)
        elif args.demo == 'post':
            example.demonstrate_post_requests(invoke_urls)
        elif args.demo == 'put':
            example.demonstrate_put_requests(invoke_urls)
        elif args.demo == 'delete':
            example.demonstrate_delete_requests(invoke_urls)
        elif args.demo == 'batch':
            example.demonstrate_batch_processing(invoke_urls)
        elif args.demo == 'error':
            example.demonstrate_error_handling_and_retries(invoke_urls)
        elif args.demo == 'lambda':
            example.demonstrate_direct_lambda_invocation()
        elif args.demo == 'parallel':
            example.demonstrate_parallel_requests(invoke_urls)
        else:  # 'all'
            example.run_all_demonstrations()
        
    except Exception as e:
        logger.error(f"Error in advanced example: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
