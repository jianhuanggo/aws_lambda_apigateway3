"""API Gateway Manager module for creating and managing API Gateway resources."""
import json
import logging
import boto3
from typing import Dict, List, Optional, Any, Tuple
from botocore.exceptions import ClientError

from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ApiGatewayManager:
    """Manager class for AWS API Gateway operations."""

    def __init__(self, config: Optional[Config] = None, profile_name: Optional[str] = None) -> None:
        """
        Initialize the API Gateway Manager.

        Args:
            config (Optional[Config]): Configuration object. If None, a default Config will be created.
            profile_name (Optional[str]): AWS profile name to use. Defaults to None.
        """
        self.config = config or Config()

        # Create a session using the profile name if provided
        session = boto3.Session(profile_name=profile_name) if profile_name else boto3.Session()

        # Use the session to create clients
        self.api_gateway_client = session.client('apigateway', **self.config.get_boto3_config())
        self.lambda_client = session.client('lambda', **self.config.get_boto3_config())

    def create_api_gateway(self, name: str, description: str = "") -> str:
        """
        Create a new API Gateway.

        Args:
            name (str): Name of the API Gateway.
            description (str): Description of the API Gateway.

        Returns:
            str: The ID of the created API Gateway.

        Raises:
            ClientError: If the API Gateway creation fails.
        """
        try:
            response = self.api_gateway_client.create_rest_api(
                name=name,
                description=description,
                endpointConfiguration={
                    'types': ['REGIONAL']
                }
            )
            api_id = response['id']
            logger.info(f"Created API Gateway with ID: {api_id}")
            return api_id
        except ClientError as e:
            logger.error(f"Failed to create API Gateway: {e}")
            raise

    def get_resources(self, api_id: str) -> List[Dict[str, Any]]:
        """
        Get all resources for an API Gateway.

        Args:
            api_id (str): The ID of the API Gateway.

        Returns:
            List[Dict[str, Any]]: List of resources.

        Raises:
            ClientError: If the resources retrieval fails.
        """
        try:
            response = self.api_gateway_client.get_resources(restApiId=api_id)
            return response['items']
        except ClientError as e:
            logger.error(f"Failed to get resources for API Gateway {api_id}: {e}")
            raise

    def get_root_resource_id(self, api_id: str) -> str:
        """
        Get the root resource ID for an API Gateway.

        Args:
            api_id (str): The ID of the API Gateway.

        Returns:
            str: The ID of the root resource.

        Raises:
            ValueError: If the root resource cannot be found.
        """
        resources = self.get_resources(api_id)
        for resource in resources:
            if resource['path'] == '/':
                return resource['id']
        raise ValueError(f"Root resource not found for API Gateway {api_id}")

    def create_resource(self, api_id: str, path_part: str, parent_id: Optional[str] = None) -> str:
        """
        Create a new resource in the API Gateway.

        Args:
            api_id (str): The ID of the API Gateway.
            path_part (str): The path part for the resource.
            parent_id (Optional[str]): The ID of the parent resource. If None, the root resource will be used.

        Returns:
            str: The ID of the created resource.

        Raises:
            ClientError: If the resource creation fails.
        """
        try:
            if parent_id is None:
                parent_id = self.get_root_resource_id(api_id)

            response = self.api_gateway_client.create_resource(
                restApiId=api_id,
                parentId=parent_id,
                pathPart=path_part
            )
            resource_id = response['id']
            logger.info(f"Created resource with ID: {resource_id} and path: /{path_part}")
            return resource_id
        except ClientError as e:
            logger.error(f"Failed to create resource for API Gateway {api_id}: {e}")
            raise

    def create_method(self, api_id: str, resource_id: str, http_method: str,
                      authorization_type: str = 'NONE') -> None:
        """
        Create a method for a resource.

        Args:
            api_id (str): The ID of the API Gateway.
            resource_id (str): The ID of the resource.
            http_method (str): The HTTP method (GET, POST, etc.).
            authorization_type (str): The authorization type.

        Raises:
            ClientError: If the method creation fails.
        """
        try:
            self.api_gateway_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                authorizationType=authorization_type,
                apiKeyRequired=False
            )
            logger.info(f"Created {http_method} method for resource {resource_id}")
        except ClientError as e:
            logger.error(f"Failed to create method for resource {resource_id}: {e}")
            raise

    def get_lambda_arn(self, function_name: str) -> str:
        """
        Get the ARN for a Lambda function.

        Args:
            function_name (str): The name of the Lambda function.

        Returns:
            str: The ARN of the Lambda function.

        Raises:
            ClientError: If the Lambda function retrieval fails.
        """
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            return response['Configuration']['FunctionArn']
        except ClientError as e:
            logger.error(f"Failed to get Lambda function {function_name}: {e}")
            raise

    def integrate_with_lambda(self, api_id: str, resource_id: str, http_method: str,
                             lambda_function_name: Optional[str] = None) -> None:
        """
        Integrate a resource method with a Lambda function.

        Args:
            api_id (str): The ID of the API Gateway.
            resource_id (str): The ID of the resource.
            http_method (str): The HTTP method (GET, POST, etc.).
            lambda_function_name (Optional[str]): The name of the Lambda function.
                If None, the default from config will be used.

        Raises:
            ClientError: If the integration fails.
        """
        try:
            function_name = lambda_function_name or self.config.lambda_function_name
            lambda_arn = self.get_lambda_arn(function_name)
            
            # Create the integration
            self.api_gateway_client.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                type='AWS',
                integrationHttpMethod='POST',
                uri=f'arn:aws:apigateway:{self.config.aws_region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations',
                contentHandling='CONVERT_TO_TEXT'
            )
            
            # Set up the integration response
            self.api_gateway_client.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                statusCode='200',
                selectionPattern=''
            )
            
            # Set up the method response
            self.api_gateway_client.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                statusCode='200',
                responseModels={
                    'application/json': 'Empty'
                }
            )
            
            logger.info(f"Integrated {http_method} method with Lambda function {function_name}")
        except ClientError as e:
            logger.error(f"Failed to integrate with Lambda function: {e}")
            raise

    def add_lambda_permission(self, lambda_function_name: Optional[str] = None,
                             api_id: Optional[str] = None) -> None:
        """
        Add permission for API Gateway to invoke the Lambda function.

        Args:
            lambda_function_name (Optional[str]): The name of the Lambda function.
                If None, the default from config will be used.
            api_id (Optional[str]): The ID of the API Gateway.
                If None, the default from config will be used.

        Raises:
            ClientError: If adding the permission fails.
        """
        try:
            function_name = lambda_function_name or self.config.lambda_function_name
            api_gateway_id = api_id or self.config.api_gateway_id
            
            # Create a unique statement ID
            statement_id = f'apigateway-{api_gateway_id}-{function_name}'
            
            # Add the permission
            self.lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=statement_id,
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{self.config.aws_region}:{self._get_account_id()}:{api_gateway_id}/*'
            )
            
            logger.info(f"Added permission for API Gateway {api_gateway_id} to invoke Lambda function {function_name}")
        except ClientError as e:
            # If the permission already exists, log a warning but don't fail
            if 'ResourceConflictException' in str(e) and 'already exists' in str(e):
                logger.warning(f"Permission already exists for API Gateway to invoke Lambda function {function_name}")
            else:
                logger.error(f"Failed to add Lambda permission: {e}")
                raise

    def _get_account_id(self) -> str:
        """
        Get the AWS account ID.

        Returns:
            str: The AWS account ID.

        Raises:
            ClientError: If the account ID retrieval fails.
        """
        try:
            sts_client = boto3.client('sts', **self.config.get_boto3_config())
            return sts_client.get_caller_identity()['Account']
        except ClientError as e:
            logger.error(f"Failed to get AWS account ID: {e}")
            raise

    def deploy_api(self, api_id: str, stage_name: str, stage_description: str = "") -> str:
        """
        Deploy the API Gateway to a stage.

        Args:
            api_id (str): The ID of the API Gateway.
            stage_name (str): The name of the stage.
            stage_description (str): The description of the stage.

        Returns:
            str: The deployment ID.

        Raises:
            ClientError: If the deployment fails.
        """
        try:
            response = self.api_gateway_client.create_deployment(
                restApiId=api_id,
                stageName=stage_name,
                description=stage_description
            )
            deployment_id = response['id']
            logger.info(f"Deployed API Gateway {api_id} to stage {stage_name} with deployment ID: {deployment_id}")
            return deployment_id
        except ClientError as e:
            logger.error(f"Failed to deploy API Gateway {api_id}: {e}")
            raise

    def get_invoke_url(self, api_id: str, stage_name: str, resource_path: str = "") -> str:
        """
        Get the invoke URL for an API Gateway resource.

        Args:
            api_id (str): The ID of the API Gateway.
            stage_name (str): The name of the stage.
            resource_path (str): The path of the resource.

        Returns:
            str: The invoke URL.
        """
        # Ensure resource_path starts with a slash if it's not empty
        if resource_path and not resource_path.startswith('/'):
            resource_path = f"/{resource_path}"
            
        return f"https://{api_id}.execute-api.{self.config.aws_region}.amazonaws.com/{stage_name}{resource_path}"
        
    def delete_resource(self, api_id: str, resource_id: str) -> None:
        """
        Delete a resource from the API Gateway.

        Args:
            api_id (str): The ID of the API Gateway.
            resource_id (str): The ID of the resource to delete.

        Raises:
            ClientError: If the resource deletion fails.
        """
        try:
            self.api_gateway_client.delete_resource(
                restApiId=api_id,
                resourceId=resource_id
            )
            logger.info(f"Deleted resource with ID: {resource_id}")
        except ClientError as e:
            logger.error(f"Failed to delete resource {resource_id}: {e}")
            raise
            
    def delete_method(self, api_id: str, resource_id: str, http_method: str) -> None:
        """
        Delete a method from a resource.

        Args:
            api_id (str): The ID of the API Gateway.
            resource_id (str): The ID of the resource.
            http_method (str): The HTTP method (GET, POST, etc.).

        Raises:
            ClientError: If the method deletion fails.
        """
        try:
            self.api_gateway_client.delete_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method
            )
            logger.info(f"Deleted {http_method} method from resource {resource_id}")
        except ClientError as e:
            logger.error(f"Failed to delete method {http_method} from resource {resource_id}: {e}")
            raise

    def get_api_gateway_by_id(self, api_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get details of an API Gateway by ID.

        Args:
            api_id (Optional[str]): The ID of the API Gateway.
                If None, the default from config will be used.

        Returns:
            Dict[str, Any]: The API Gateway details.

        Raises:
            ClientError: If the API Gateway retrieval fails.
        """
        try:
            api_gateway_id = api_id or self.config.api_gateway_id
            response = self.api_gateway_client.get_rest_api(restApiId=api_gateway_id)
            return response
        except ClientError as e:
            logger.error(f"Failed to get API Gateway {api_gateway_id}: {e}")
            raise

    def find_resource_by_path(self, api_id: str, path: str) -> Optional[Dict[str, Any]]:
        """
        Find a resource by its path.

        Args:
            api_id (str): The ID of the API Gateway.
            path (str): The path of the resource.

        Returns:
            Optional[Dict[str, Any]]: The resource details, or None if not found.
        """
        try:
            resources = self.get_resources(api_id)
            for resource in resources:
                if resource['path'] == path:
                    return resource
            return None
        except ClientError as e:
            logger.error(f"Failed to find resource by path {path}: {e}")
            raise

    def create_or_update_api_gateway(self,
                                     api_name: str,
                                     resource_path: str,
                                     http_method: str,
                                     stage_name: str = 'prod',
                                     lambda_function_name: Optional[str] = None) -> Tuple[str, str]:
        """
        Create or update an API Gateway with a resource and method integrated with a Lambda function.

        Args:
            api_name (str): The name of the API Gateway.
            resource_path (str): The path of the resource.
            http_method (str): The HTTP method (GET, POST, etc.).
            stage_name (str): The name of the stage to deploy to. Defaults to 'prod'.
            lambda_function_name (Optional[str]): The name of the Lambda function.
                If None, the default from config will be used.

        Returns:
            Tuple[str, str]: The API Gateway ID and the invoke URL.
        """
        # Use the provided Lambda function name or the default from config
        function_name = lambda_function_name or self.config.lambda_function_name
        
        try:
            # Try to use the existing API Gateway from config
            api_id = self.config.api_gateway_id
            self.get_api_gateway_by_id(api_id)
            logger.info(f"Using existing API Gateway with ID: {api_id}")
        except ClientError:
            # Create a new API Gateway if the existing one is not found
            logger.info(f"Creating new API Gateway with name: {api_name}")
            api_id = self.create_api_gateway(api_name)
        
        # Check if the resource already exists
        resource = self.find_resource_by_path(api_id, f"/{resource_path}")
        if resource:
            resource_id = resource['id']
            logger.info(f"Found existing resource with ID: {resource_id}")
            
            # Delete the existing method if it exists
            try:
                self.delete_method(api_id, resource_id, http_method)
                logger.info(f"Deleted existing method {http_method} for resource {resource_id}")
            except ClientError as e:
                # If the method doesn't exist, that's fine
                if 'NotFoundException' in str(e):
                    logger.info(f"Method {http_method} does not exist for resource {resource_id}")
                else:
                    # For other errors, log and continue
                    logger.warning(f"Error deleting method {http_method} for resource {resource_id}: {e}")
            
            # Delete the existing resource
            try:
                self.delete_resource(api_id, resource_id)
                logger.info(f"Deleted existing resource with ID: {resource_id}")
            except ClientError as e:
                # Log the error but continue with creation
                logger.warning(f"Error deleting resource {resource_id}: {e}")
        
        # Create a new resource
        resource_id = self.create_resource(api_id, resource_path)
        
        # Create the method and integrate with Lambda
        self.create_method(api_id, resource_id, http_method)
        self.integrate_with_lambda(api_id, resource_id, http_method, function_name)
        self.add_lambda_permission(function_name, api_id)
        
        # Deploy the API
        self.deploy_api(api_id, stage_name)
        
        # Get the invoke URL
        invoke_url = self.get_invoke_url(api_id, stage_name, resource_path)
        
        return api_id, invoke_url

    def create_or_update_api_gateway2(self,
                                     api_name: str,
                                     resource_path: str,
                                     http_method: str,
                                     stage_name: str = 'prod',
                                     lambda_function_name: Optional[str] = None) -> Tuple[str, str]:
        """
        Create or update an API Gateway with a resource and method integrated with a Lambda function.

        Args:
            api_name (str): The name of the API Gateway.
            resource_path (str): The path of the resource.
            http_method (str): The HTTP method (GET, POST, etc.).
            stage_name (str): The name of the stage to deploy to. Defaults to 'prod'.
            lambda_function_name (Optional[str]): The name of the Lambda function.
                If None, the default from config will be used.

        Returns:
            Tuple[str, str]: The API Gateway ID and the invoke URL.
        """
        # Use the provided Lambda function name or the default from config
        function_name = lambda_function_name or self.config.lambda_function_name

        try:
            # Try to use the existing API Gateway from config
            api_id = self.config.api_gateway_id
            self.get_api_gateway_by_id(api_id)
            logger.info(f"Using existing API Gateway with ID: {api_id}")
        except ClientError:
            # Create a new API Gateway if the existing one is not found
            logger.info(f"Creating new API Gateway with name: {api_name}")
            api_id = self.create_api_gateway(api_name)

        # Check if the resource already exists
        resource = self.find_resource_by_path(api_id, f"/{resource_path}")
        if resource:
            resource_id = resource['id']
            logger.info(f"Found existing resource with ID: {resource_id}")

            # Delete the existing method if it exists
            try:
                self.delete_method(api_id, resource_id, http_method)
                logger.info(f"Deleted existing method {http_method} for resource {resource_id}")
            except ClientError as e:
                # If the method doesn't exist, that's fine
                if 'NotFoundException' in str(e):
                    logger.info(f"Method {http_method} does not exist for resource {resource_id}")
                else:
                    # For other errors, log and continue
                    logger.warning(f"Error deleting method {http_method} for resource {resource_id}: {e}")

            # Delete the existing resource
            try:
                self.delete_resource(api_id, resource_id)
                logger.info(f"Deleted existing resource with ID: {resource_id}")
            except ClientError as e:
                # Log the error but continue with creation
                logger.warning(f"Error deleting resource {resource_id}: {e}")

        # Create a new resource
        resource_id = self.create_resource(api_id, resource_path)

        # Create the method and integrate with Lambda
        self.create_method(api_id, resource_id, http_method)
        self.integrate_with_lambda(api_id, resource_id, http_method, function_name)
        self.add_lambda_permission(function_name, api_id)

        # Deploy the API
        self.deploy_api(api_id, stage_name)

        # Get the invoke URL
        invoke_url = self.get_invoke_url(api_id, stage_name, resource_path)

        return api_id, invoke_url