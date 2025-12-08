import boto3
from loguru import logger

from agentcore_agents.config import settings


def get_secret_name(gateway_name: str) -> str:
    return f"agentcore-gateway-{gateway_name.lower()}-cognito-client-secret"


def store_client_secret(gateway_name: str, client_secret: str, region: str | None = None) -> None:
    region = region or settings.aws.region
    secrets_client = boto3.client("secretsmanager", region_name=region)
    secret_name = get_secret_name(gateway_name)

    try:
        secrets_client.create_secret(
            Name=secret_name,
            Description=f"Cognito client secret for AgentCore Gateway: {gateway_name}",
            SecretString=client_secret,
        )
        logger.info(f"Stored client secret in Secrets Manager: {secret_name}")
    except secrets_client.exceptions.ResourceExistsException:
        secrets_client.update_secret(
            SecretId=secret_name,
            SecretString=client_secret,
        )
        logger.info(f"Updated client secret in Secrets Manager: {secret_name}")
    except Exception as e:
        logger.error(f"Error storing secret: {e}")
        raise


def get_client_secret(gateway_name: str, region: str | None = None) -> str:
    region = region or settings.aws.region
    secrets_client = boto3.client("secretsmanager", region_name=region)
    secret_name = get_secret_name(gateway_name)

    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        client_secret = response["SecretString"]
        logger.info(f"Retrieved client secret from Secrets Manager: {secret_name}")
        return client_secret
    except secrets_client.exceptions.ResourceNotFoundException:
        logger.warning(f"Secret not found: {secret_name}")
        raise
    except Exception as e:
        logger.error(f"Error retrieving secret: {e}")
        raise


def delete_client_secret(gateway_name: str, region: str | None = None) -> None:
    region = region or settings.aws.region
    secrets_client = boto3.client("secretsmanager", region_name=region)
    secret_name = get_secret_name(gateway_name)

    try:
        secrets_client.delete_secret(
            SecretId=secret_name,
            ForceDeleteWithoutRecovery=True,
        )
        logger.info(f"Deleted secret from Secrets Manager: {secret_name}")
    except secrets_client.exceptions.ResourceNotFoundException:
        logger.warning(f"Secret not found, skipping deletion: {secret_name}")
    except Exception as e:
        logger.error(f"Error deleting secret: {e}")
        raise
