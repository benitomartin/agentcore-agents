import boto3
from botocore.exceptions import ClientError
from loguru import logger

from agentcore_agents.auth.secrets_manager import delete_client_secret, get_client_secret
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

    role_name = settings.lambda_settings.role_name
    try:
        logger.info(f"Deleting IAM role: {role_name}")

        inline_policies = iam_client.list_role_policies(RoleName=role_name)
        for policy_name in inline_policies.get("PolicyNames", []):
            logger.info(f"  Deleting inline policy: {policy_name}")
            iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
        for policy in attached_policies.get("AttachedPolicies", []):
            logger.info(f"  Detaching managed policy: {policy['PolicyArn']}")
            iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])

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

    setup = GatewaySetup()
    gateway_name = settings.gateway.name

    try:
        gateway_info = setup.get_gateway_info(gateway_name)
        client_info = setup.get_client_info_from_gateway(gateway_name)
    except ValueError as e:
        logger.error(f"Gateway not found: {e}")
        logger.info("Nothing to clean up")
        return

    logger.info("Retrieving client secret from Secrets Manager for cleanup...")
    try:
        client_secret = get_client_secret(gateway_name, setup.region)
        client_info["client_secret"] = client_secret
    except Exception as e:
        logger.warning(f"Could not retrieve client secret: {e}")
        logger.warning("Continuing cleanup without client secret...")

    logger.info(f"Cleaning up gateway: {gateway_info['gateway_id']}")
    setup.cleanup_gateway(gateway_info["gateway_id"], client_info)

    logger.info("Deleting client secret from Secrets Manager...")
    try:
        delete_client_secret(gateway_name, setup.region)
    except Exception as e:
        logger.warning(f"Could not delete secret: {e}")

    logger.info("Cleaning up Lambda function")
    try:
        lambda_arn = setup.get_lambda_arn()
        cleanup_lambda(lambda_arn, setup.region)
    except ValueError as e:
        logger.warning(f"Could not retrieve Lambda ARN: {e}")
        logger.warning("Skipping Lambda cleanup")

    logger.info("Gateway cleanup completed successfully")


if __name__ == "__main__":
    main()
