"""Configuration module for API Gateway Lambda integration."""
import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for API Gateway Lambda integration."""

    def __init__(self, profile_name: Optional[str] = None) -> None:
        """
        Initialize configuration with environment variables or AWS profile.

        Args:
            profile_name (Optional[str]): AWS profile name to use. Defaults to None.
                If provided, this will take precedence over AWS credentials from environment variables.
        """
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.api_gateway_id = os.getenv("API_GATEWAY_ID", "5321hipmwk")
        self.lambda_function_name = os.getenv("LAMBDA_FUNCTION_NAME", "lambda-pg_api_metadata")
        self.profile_name = profile_name or os.getenv("AWS_PROFILE")

    def get_boto3_config(self) -> Dict[str, Optional[str]]:
        """
        Get boto3 configuration dictionary.

        Returns:
            Dict[str, Optional[str]]: Dictionary with AWS configuration.
        """
        config: Dict[str, Optional[str]] = {
            "region_name": self.aws_region,
        }

        # If a profile is specified, use it
        if self.profile_name:
            config["profile_name"] = self.profile_name
        # Otherwise, use credentials if provided
        elif self.aws_access_key_id and self.aws_secret_access_key:
            config.update({
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key,
            })

        return config
