import base64
import hashlib
import hmac

import boto3
from loguru import logger

from agentcore_agents.config import settings


def compute_secret_hash(client_id: str, client_secret: str, username: str) -> str:
    message = username + client_id
    dig = hmac.new(
        client_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode("utf-8")


def create_cognito_user(user_pool_id: str, username: str, password: str, email: str) -> None:
    cognito = boto3.client("cognito-idp", region_name=settings.aws.region)

    try:
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
            ],
            MessageAction="SUPPRESS",
        )
        logger.info(f"Created user: {username}")
    except cognito.exceptions.UsernameExistsException:
        logger.info(f"User {username} already exists")

    try:
        cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=password,
            Permanent=True,
        )
        logger.info(f"Set password for user: {username}")
    except Exception as e:
        logger.warning(f"Could not set password (might already be set): {e}")


def update_cognito_client_for_user_auth(user_pool_id: str, client_id: str) -> None:
    cognito = boto3.client("cognito-idp", region_name=settings.aws.region)

    logger.info("Updating Cognito client to support USER_PASSWORD_AUTH...")
    try:
        cognito.update_user_pool_client(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            ExplicitAuthFlows=["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"],
        )
        logger.info("✓ Cognito client updated")
    except Exception as e:
        logger.warning(f"Could not update client: {e}")


def get_user_token(
    client_id: str,
    client_secret: str,
    username: str,
    password: str,
) -> dict[str, str]:
    cognito = boto3.client("cognito-idp", region_name=settings.aws.region)

    logger.info(f"Authenticating user {username}...")

    secret_hash = compute_secret_hash(client_id, client_secret, username)

    try:
        response = cognito.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password,
                "SECRET_HASH": secret_hash,
            },
        )

        access_token = response["AuthenticationResult"]["AccessToken"]
        id_token = response["AuthenticationResult"]["IdToken"]

        logger.info("✓ Got user tokens")

        return {
            "access_token": access_token,
            "id_token": id_token,
            "token_type": "Bearer",
        }
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        raise
