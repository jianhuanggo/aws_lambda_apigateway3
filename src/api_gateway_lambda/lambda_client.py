"""Lambda Client module for invoking Lambda functions."""
import json
import logging
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LambdaClient:
    """Client class for AWS Lambda operations."""

    def __init__(self, config: Optional[Config] = None, profile_name: Optional[str] = None) -> None:
        """
        Initialize the Lambda Client.

        Args:
            config (Optional[Config]): Configuration object. If None, a default Config will be created.
            profile_name (Optional[str]): AWS profile name to use. Defaults to None.
        """
        self.config = config or Config(profile_name=profile_name)
        self.lambda_client = boto3.client('lambda', **self.config.get_boto3_config())

    def invoke_lambda(self, function_name: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Invoke a Lambda function.

        Args:
            function_name (Optional[str]): The name of the Lambda function.
                If None, the default from config will be used.
            payload (Optional[Dict[str, Any]]): The payload to send to the Lambda function.
                If None, an empty dict will be used.

        Returns:
            Dict[str, Any]: The response from the Lambda function.

        Raises:
            ClientError: If the Lambda invocation fails.
        """
        try:
            # Use the provided function name or the default from config
            lambda_function = function_name or self.config.lambda_function_name
            
            # Use the provided payload or an empty dict
            lambda_payload = payload or {}
            
            # Invoke the Lambda function
            response = self.lambda_client.invoke(
                FunctionName=lambda_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(lambda_payload)
            )
            
            # Parse the response payload
            response_payload = json.loads(response['Payload'].read().decode('utf-8'))
            
            logger.info(f"Successfully invoked Lambda function {lambda_function}")
            return response_payload
        except ClientError as e:
            logger.error(f"Failed to invoke Lambda function {function_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing Lambda response: {e}")
            raise

    def get_lambda_function_info(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a Lambda function.

        Args:
            function_name (Optional[str]): The name of the Lambda function.
                If None, the default from config will be used.

        Returns:
            Dict[str, Any]: Information about the Lambda function.

        Raises:
            ClientError: If the Lambda function retrieval fails.
        """
        try:
            # Use the provided function name or the default from config
            lambda_function = function_name or self.config.lambda_function_name
            
            # Get the Lambda function information
            response = self.lambda_client.get_function(FunctionName=lambda_function)
            
            logger.info(f"Successfully retrieved information for Lambda function {lambda_function}")
            return response
        except ClientError as e:
            logger.error(f"Failed to get Lambda function {function_name}: {e}")
            raise
