import json
import time
import zipfile
from io import BytesIO
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from agentcore_agents.config import settings


def load_tool_schema() -> dict:
    schema_path = Path("src/agentcore_agents/lambda/tool_schema.json")
    with schema_path.open() as f:
        schema_data = json.load(f)

    return {
        "inlinePayload": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["inputSchema"],
            }
            for tool in schema_data["tools"]
        ]
    }


def create_lambda_role(lambda_client: boto3.client, iam_client: boto3.client) -> str:
    role_name = settings.lambda_settings.role_name

    try:
        role = iam_client.get_role(RoleName=role_name)
        logger.info(f"Role {role_name} already exists")
        role_arn = role["Role"]["Arn"]
    except iam_client.exceptions.NoSuchEntityException:
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }

        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for AgentCore Gateway Lambda function",
        )
        role_arn = role["Role"]["Arn"]
        logger.info(f"Created role: {role_arn}")
        logger.info("Waiting for IAM role to propagate...")
        time.sleep(5)

    iam_client.attach_role_policy(
        RoleName=role_name,
        PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    s3_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket",
                ],
                "Resource": [
                    f"arn:aws:s3:::{settings.s3.documents_bucket}",
                    f"arn:aws:s3:::{settings.s3.documents_bucket}/*",
                ],
            }
        ],
    }

    policy_name = "S3DocumentsBucketAccess"
    try:
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(s3_policy),
        )
        logger.info(f"Added S3 access policy to role {role_name}")
    except ClientError as e:
        logger.warning(f"Failed to add S3 policy: {e}")

    return role_arn


def package_lambda_code() -> bytes:
    handler_path = Path("src/agentcore_agents/lambda/handler.py")

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(handler_path, "handler.py")

    zip_buffer.seek(0)
    return zip_buffer.read()


def deploy_lambda(
    function_name: str | None = None,
    lambda_arn: str | None = None,
) -> str:
    if function_name is None:
        function_name = settings.lambda_settings.function_name
    lambda_client = boto3.client("lambda", region_name=settings.aws.region)
    iam_client = boto3.client("iam", region_name=settings.aws.region)

    role_arn = create_lambda_role(lambda_client, iam_client)
    code = package_lambda_code()

    if lambda_arn:
        function_name = lambda_arn.split(":")[-1]
        logger.info(f"Updating existing Lambda: {function_name}")
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=code,
        )
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Timeout=settings.lambda_settings.timeout,
            MemorySize=settings.lambda_settings.memory_size,
            Environment={
                "Variables": {
                    "S3_DOCUMENTS_BUCKET": settings.s3.documents_bucket,
                }
            },
        )
        logger.info(f"Lambda updated: {lambda_arn}")
        return lambda_arn

    try:
        existing = lambda_client.get_function(FunctionName=function_name)
        logger.info(f"Lambda {function_name} already exists, updating...")

        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=code,
        )

        logger.info("Waiting for code update to complete...")
        waiter = lambda_client.get_waiter("function_updated")
        waiter.wait(
            FunctionName=function_name,
            WaiterConfig={"Delay": 2, "MaxAttempts": 30},
        )

        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Timeout=settings.lambda_settings.timeout,
            MemorySize=settings.lambda_settings.memory_size,
            Environment={
                "Variables": {
                    "S3_DOCUMENTS_BUCKET": settings.s3.documents_bucket,
                }
            },
        )

        logger.info("Waiting for configuration update to complete...")
        waiter.wait(
            FunctionName=function_name,
            WaiterConfig={"Delay": 2, "MaxAttempts": 30},
        )

        return existing["Configuration"]["FunctionArn"]
    except lambda_client.exceptions.ResourceNotFoundException:
        pass

    logger.info(f"Creating Lambda function: {function_name}")

    max_retries = 3
    retry_delay = 5
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime="python3.13",
                Role=role_arn,
                Handler="handler.lambda_handler",
                Code={"ZipFile": code},
                Description=(
                    "AgentCore Gateway tools Lambda "
                    "(calculator, get_current_time, read_s3_document)"
                ),
                Timeout=settings.lambda_settings.timeout,
                MemorySize=settings.lambda_settings.memory_size,
                Environment={
                    "Variables": {
                        "S3_DOCUMENTS_BUCKET": settings.s3.documents_bucket,
                    }
                },
            )

            created_arn: str = response["FunctionArn"]
            logger.info(f"Lambda created: {created_arn}")
            return created_arn

        except ClientError as e:
            last_error = e
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "InvalidParameterValueException" and attempt < max_retries - 1:
                logger.warning(
                    f"Role not yet assumable (attempt {attempt + 1}/{max_retries}), "
                    f"waiting {retry_delay} seconds..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Failed to create Lambda function: {e}")
                raise

    if last_error:
        raise RuntimeError("Failed to create Lambda function after all retries") from last_error
    raise RuntimeError("Failed to create Lambda function after all retries")


def main() -> None:
    logger.info("Deploying Lambda function for Gateway tools")

    lambda_arn = deploy_lambda()

    logger.info(f"Lambda ARN: {lambda_arn}")
    logger.info("\nNext steps:")
    logger.info("1. Run setup_gateway.py to add this Lambda to your Gateway")
    logger.info("2. The Lambda ARN and tool schema will be retrieved automatically from AWS")


if __name__ == "__main__":
    main()
