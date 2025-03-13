"""API Client module for making requests to API Gateway endpoints."""
import json
import logging
import requests
from typing import Dict, Any, Optional, Union

from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ApiClient:
    """Client class for making requests to API Gateway endpoints."""

    def __init__(self, config: Optional[Config] = None, profile_name: Optional[str] = None) -> None:
        """
        Initialize the API Client.

        Args:
            config (Optional[Config]): Configuration object. If None, a default Config will be created.
            profile_name (Optional[str]): AWS profile name to use. Defaults to None.
        """
        self.config = config or Config(profile_name=profile_name)

    def make_request(self, url: str, method: str = 'GET', 
                    headers: Optional[Dict[str, str]] = None,
                    params: Optional[Dict[str, Any]] = None,
                    data: Optional[Union[Dict[str, Any], str]] = None,
                    timeout: int = 30) -> Dict[str, Any]:
        """
        Make a request to an API Gateway endpoint.

        Args:
            url (str): The URL of the API Gateway endpoint.
            method (str): The HTTP method (GET, POST, etc.).
            headers (Optional[Dict[str, str]]): The headers to include in the request.
            params (Optional[Dict[str, Any]]): The query parameters to include in the request.
            data (Optional[Union[Dict[str, Any], str]]): The data to include in the request body.
            timeout (int): The request timeout in seconds.

        Returns:
            Dict[str, Any]: The response from the API Gateway endpoint.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        try:
            # Set default headers if none provided
            if headers is None:
                headers = {'Content-Type': 'application/json'}
            
            # Convert dict data to JSON string if needed
            if isinstance(data, dict):
                data = json.dumps(data)
            
            # Make the request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                timeout=timeout
            )
            
            # Raise an exception for HTTP errors
            response.raise_for_status()
            
            # Try to parse the response as JSON
            try:
                result = response.json()
            except json.JSONDecodeError:
                # If the response is not JSON, return the text
                result = {'text': response.text}
            
            logger.info(f"Successfully made {method} request to {url}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
            raise
