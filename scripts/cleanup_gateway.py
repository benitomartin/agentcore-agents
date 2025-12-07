import json
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from agentcore_agents.config import settings
from agentcore_agents.gateway.setup import GatewaySetup


def cleanup_lambda(lambda_arn: str, region: str) -> None:
    lambda_client = boto3.client("lambda", region_name=region)
    iam_client = boto3.client("iam", region_name=region)
    
    function_name = lambda_arn.split(":")[-1]
    
    try:
        logger.info(f"Deleting Lambda function: {function_name}")
        lambda_client.delete_function(FunctionName=function_name)
        logger.info(f"Lambda function deleted: {function_name}")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "ResourceNotFoundException":
            logger.warning(f"Lambda function {function_name} not found, skipping")
        else:
            logger.error(f"Error deleting Lambda function: {e}")
            raise
    
    role_name = "AgentCoreGatewayLambdaRole"
    try:
        logger.info(f"Deleting IAM role: {role_name}")
        
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
        for policy in attached_policies.get("AttachedPolicies", []):
            iam_client.detach_role_policy(
                RoleName=role_name, PolicyArn=policy["PolicyArn"]
            )
        
        iam_client.delete_role(RoleName=role_name)
        logger.info(f"IAM role deleted: {role_name}")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "NoSuchEntity":
            logger.warning(f"IAM role {role_name} not found, skipping")
        else:
            logger.error(f"Error deleting IAM role: {e}")
            raise


def main() -> None:
    logger.info("Starting Gateway cleanup")

    config_path = Path("gateway_config.json")
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        logger.info("Nothing to clean up")
        return

    with config_path.open() as f:
        config = json.load(f)

    setup = GatewaySetup(region=config["region"])

    logger.info(f"Cleaning up gateway: {config['gateway_id']}")
    setup.cleanup_gateway(config["gateway_id"], config["client_info"])

    config_path.unlink()
    logger.info(f"Deleted config file: {config_path}")

    lambda_config_path = Path("lambda_config.json")
    if lambda_config_path.exists():
        logger.info("Cleaning up Lambda function")
        with lambda_config_path.open() as f:
            lambda_config = json.load(f)
        
        lambda_arn = lambda_config.get("lambda_arn")
        region = lambda_config.get("region", config.get("region", settings.aws.region))
        
        if lambda_arn:
            cleanup_lambda(lambda_arn, region)
        else:
            logger.warning("No lambda_arn found in lambda_config.json")
        
        lambda_config_path.unlink()
        logger.info(f"Deleted Lambda config file: {lambda_config_path}")

    logger.info("Gateway cleanup completed successfully")


if __name__ == "__main__":
    main()
