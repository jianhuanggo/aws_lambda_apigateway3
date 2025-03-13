# AWS Lambda API Gateway Integration

This project provides a production-grade Python implementation for integrating AWS API Gateway with Lambda functions using the boto3 SDK.

## Overview

This package allows you to:
1. Create and configure API Gateway endpoints
2. Connect API Gateway endpoints to Lambda functions
3. Make REST calls to execute Lambda functions and retrieve results

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file based on the `.env.example` template and add your AWS credentials:

```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
API_GATEWAY_ID=5321hipmwk
LAMBDA_FUNCTION_NAME=lambda-pg_api_metadata
AWS_PROFILE=your_profile_name
```

You can use either AWS credentials (access key and secret key) or an AWS profile for authentication. If both are provided, the AWS profile takes precedence.

## Usage

### Basic Usage

```python
from src.api_gateway_lambda.api_gateway_manager import ApiGatewayManager

# Initialize the manager
api_manager = ApiGatewayManager()

# Create an API Gateway endpoint connected to a Lambda function
api_id, invoke_url = api_manager.create_or_update_api_gateway(
    api_name="MyAPI",
    resource_path="my-resource",
    http_method="GET"
)

print(f"API Gateway endpoint URL: {invoke_url}")
```

### Calling the API Gateway Endpoint

```python
from src.api_gateway_lambda.api_client import ApiClient

# Initialize the client
api_client = ApiClient()

# Make a request to the API Gateway endpoint
response = api_client.make_request(
    url="https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/my-resource",
    method="GET"
)

print(f"Response: {response}")
```

### Direct Lambda Invocation

```python
from src.api_gateway_lambda.lambda_client import LambdaClient

# Initialize the client
lambda_client = LambdaClient()

# Invoke the Lambda function directly
response = lambda_client.invoke_lambda(
    payload={"key": "value"}
)

print(f"Response: {response}")
```

### Command Line Interface

The package provides a command-line interface for interacting with AWS API Gateway and Lambda functions.

#### Installation

```bash
# Install the package in development mode
pip install -e .
```

After installation, the `aws-lambda-api` command will be available in your environment.
#### AWS Profile Support

The package supports using AWS profiles for authentication. You can specify a profile name when using the CLI:

```bash
# Use the "latest" AWS profile
aws-lambda-api create-api --api-name "MyAPI" --resource-path "my-resource" --profile "latest"

# Invoke a Lambda function with a specific profile
aws-lambda-api invoke-lambda --function-name "my-function" --payload '{"key": "value"}' --profile "latest"

# Call an API Gateway endpoint with a specific profile
aws-lambda-api call-api --resource-path "my-resource" --profile "latest"
```

By default, all commands use the "latest" profile if no profile is specified.

#### Available Commands

```bash
# Show help
aws-lambda-api --help

# Create or update an API Gateway
aws-lambda-api create-api --api-name "MyAPI" --resource-path "my-resource" --http-method "GET"

# Invoke a Lambda function directly
aws-lambda-api invoke-lambda --function-name "my-function" --payload '{"key": "value"}'

# Call an API Gateway endpoint
aws-lambda-api call-api --resource-path "my-resource" --http-method "GET"

# List resources for an API Gateway
aws-lambda-api list-resources

# Delete a resource from an API Gateway
aws-lambda-api delete-resource --resource-path "/my-resource"
```

#### Command Details

1. **create-api**: Create or update an API Gateway endpoint
   ```bash
   aws-lambda-api create-api --api-name "MyAPI" --resource-path "my-resource" --http-method "GET" --stage "prod" --function-name "my-function"
   ```
   - `--api-name`: Name of the API Gateway (required)
   - `--resource-path`: Resource path (required)
   - `--http-method`: HTTP method (default: GET)
   - `--stage`: API Gateway stage (default: prod)
   - `--function-name`: Lambda function name (defaults to config)

2. **invoke-lambda**: Invoke a Lambda function directly
   ```bash
   aws-lambda-api invoke-lambda --function-name "my-function" --payload '{"key": "value"}'
   ```
   - `--function-name`: Lambda function name (defaults to config)
   - `--payload`: JSON payload to send to the Lambda function

3. **call-api**: Call an API Gateway endpoint
   ```bash
   aws-lambda-api call-api --api-id "your-api-id" --resource-path "my-resource" --http-method "GET" --stage "prod" --data '{"key": "value"}'
   ```
   - `--api-id`: API Gateway ID (defaults to config)
   - `--resource-path`: Resource path (required)
   - `--http-method`: HTTP method (default: GET)
   - `--stage`: API Gateway stage (default: prod)
   - `--data`: JSON data to send in the request body

4. **list-resources**: List resources for an API Gateway
   ```bash
   aws-lambda-api list-resources --api-id "your-api-id"
   ```
   - `--api-id`: API Gateway ID (defaults to config)

5. **delete-resource**: Delete a resource from an API Gateway
   ```bash
   aws-lambda-api delete-resource --api-id "your-api-id" --resource-id "resource-id"
   # OR
   aws-lambda-api delete-resource --api-id "your-api-id" --resource-path "/my-resource"
   ```
   - `--api-id`: API Gateway ID (defaults to config)
   - `--resource-id`: Resource ID to delete
   - `--resource-path`: Resource path to delete (alternative to resource-id)

## Examples

The `examples` directory contains several scripts demonstrating different aspects of the package:

- `create_api_gateway.py`: Creates an API Gateway endpoint integrated with a Lambda function
- `invoke_lambda.py`: Invokes a Lambda function directly
- `call_api_gateway.py`: Makes a request to an API Gateway endpoint
- `complete_example.py`: Demonstrates the full workflow from creation to invocation
- `advanced_example.py`: Showcases advanced features including multiple resources, HTTP methods, error handling, and parallel requests

To run an example:

```bash
cd examples
python create_api_gateway.py
```

## Testing

Run the tests with pytest:

```bash
pytest
```

For more detailed test output:

```bash
pytest -v
```

To generate a coverage report:

```bash
coverage run -m pytest
coverage report
```

## Project Structure

```
aws_lambda_apigateway/
├── .env.example           # Example environment variables
├── .gitignore             # Git ignore file
├── README.md              # Project documentation
├── requirements.txt       # Project dependencies
├── setup.py               # Package setup file
├── src/                   # Source code
│   └── api_gateway_lambda/
│       ├── __init__.py
│       ├── api_client.py          # Client for making API requests
│       ├── api_gateway_manager.py # Manager for API Gateway operations
│       ├── config.py              # Configuration module
│       └── lambda_client.py       # Client for Lambda operations
├── tests/                 # Unit tests
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── test_api_client.py        # Tests for ApiClient
│   ├── test_api_gateway_manager.py # Tests for ApiGatewayManager
│   ├── test_config.py            # Tests for Config
│   └── test_lambda_client.py     # Tests for LambdaClient
└── examples/              # Example scripts
    ├── call_api_gateway.py       # Example of calling an API Gateway
    ├── complete_example.py       # Complete workflow example
    ├── create_api_gateway.py     # Example of creating an API Gateway
    └── invoke_lambda.py          # Example of invoking a Lambda function
```

## License

MIT
