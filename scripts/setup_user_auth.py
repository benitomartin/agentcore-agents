import json
from pathlib import Path

from loguru import logger

from agentcore_agents.auth.cognito import (
    create_cognito_user,
    get_user_token,
    update_cognito_client_for_user_auth,
)
from agentcore_agents.auth.secrets_manager import get_client_secret
from agentcore_agents.auth.user_identity import decode_jwt_payload
from agentcore_agents.config import settings
from agentcore_agents.gateway.setup import GatewaySetup


def main() -> None:
    logger.info("Setting up user authentication for Gateway Inbound Auth")

    setup = GatewaySetup()
    gateway_name = settings.gateway.name

    try:
        client_info = setup.get_client_info_from_gateway(gateway_name)
    except ValueError as e:
        logger.error(f"Gateway not found: {e}")
        logger.info("Run setup_gateway.py first")
        return

    user_pool_id = client_info["user_pool_id"]
    client_id = client_info["client_id"]

    logger.info("Retrieving client secret from Secrets Manager...")
    client_secret = get_client_secret(gateway_name, setup.region)

    username = "testuser"
    password = "TestPassword123!"
    email = "testuser@example.com"

    logger.info("Step 1: Updating Cognito client to support user authentication...")
    update_cognito_client_for_user_auth(user_pool_id, client_id)

    logger.info("\nStep 2: Creating Cognito user...")
    create_cognito_user(user_pool_id, username, password, email)

    logger.info("\nStep 3: Getting user access token...")
    token_data = get_user_token(client_id, client_secret, username, password)
    access_token = token_data.get("access_token")

    logger.info("\nStep 4: Decoding JWT to see user identity claims...")
    access_token_str = access_token if isinstance(access_token, str) else ""
    jwt_payload = decode_jwt_payload(access_token_str)
    logger.info(f"JWT payload: {json.dumps(jwt_payload, indent=2)}")

    user_sub = jwt_payload.get("sub", "")
    user_email = jwt_payload.get("email", "")
    logger.info("\nUser identity from JWT:")
    logger.info(f"  sub (user ID): {user_sub}")
    logger.info(f"  email: {user_email}")

    user_config = {
        "username": username,
        "password": password,
        "email": email,
        "user_sub": user_sub,
        "access_token": access_token,
        "token_data": token_data,
        "user_pool_id": user_pool_id,
        "client_id": client_id,
    }

    config_path_user = Path("user_auth_config.json")
    with config_path_user.open("w") as f:
        json.dump(user_config, f, indent=2)

    logger.info(f"\n✓ User authentication config saved to: {config_path_user}")



if __name__ == "__main__":
    main()
