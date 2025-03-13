from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="aws_lambda_apigateway",
    version="0.1.0",
    author="Jian Huang",
    author_email="jianhuanggo@example.com",
    description="AWS Lambda API Gateway Integration using boto3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jianhuanggo/aws_lambda_apigateway",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'aws-lambda-api=api_gateway_lambda.cli:main',
        ],
    },
)
