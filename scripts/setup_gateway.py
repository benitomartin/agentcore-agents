from loguru import logger

from agentcore_agents.auth.secrets_manager import store_client_secret
from agentcore_agents.config import settings
from agentcore_agents.gateway.setup import GatewaySetup


def main() -> None:
    logger.info("Starting Gateway setup with Cognito OAuth")

    setup = GatewaySetup()
    gateway_name = settings.gateway.name

    existing_gateway = setup._find_gateway_by_name(gateway_name)
    if existing_gateway:
        logger.info(f"Gateway '{gateway_name}' already exists")
        logger.info("Skipping setup. Gateway is already configured.")
        return

    logger.info("Step 1: Creating new OAuth authorizer with Cognito")
    cognito_response = setup.create_oauth_with_cognito(gateway_name)

    client_secret = cognito_response.get("client_info", {}).get("client_secret")
    if client_secret:
        logger.info("Step 1a: Storing client secret in AWS Secrets Manager...")
        store_client_secret(gateway_name, client_secret, setup.region)

    logger.info("Step 2: Creating MCP Gateway with Inbound Auth")
    logger.info("  - Inbound Auth: JWT validation via Cognito User Pool")
    logger.info("  - Only authenticated users/clients can access Lambda tools")
    gateway = setup.get_or_create_gateway(
        authorizer_config=cognito_response["authorizer_config"], name=gateway_name
    )

    logger.info("Step 3: Getting or creating Lambda target")

    logger.info("Retrieving Lambda ARN from AWS...")
    try:
        lambda_arn = setup.get_lambda_arn()
    except ValueError as e:
        logger.error(str(e))
        return

    logger.info("Loading tool schema...")
    try:
        tool_schema = setup.load_tool_schema()
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    logger.info(f"Using Lambda: {lambda_arn}")
    setup.get_or_create_lambda_target(
        gateway,
        name=settings.gateway.lambda_target_name,
        lambda_arn=lambda_arn,
        tool_schema=tool_schema,
    )

    logger.info("=" * 60)
    logger.info("Gateway Setup Complete!")
    logger.info(f"Gateway ID: {gateway['gatewayId']}")
    logger.info(f"Gateway URL: {gateway['gatewayUrl']}")
    logger.info("Cognito configured successfully")
    logger.info("All configuration stored in AWS (Secrets Manager + Gateway)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
