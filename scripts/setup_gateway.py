import json
from pathlib import Path

from loguru import logger

from agentcore_agents.gateway.setup import GatewaySetup


def main() -> None:
    logger.info("Starting Gateway setup with Cognito OAuth")

    setup = GatewaySetup()

    config_path = Path("gateway_config.json")
    existing_config = None
    if config_path.exists():
        logger.info("Found existing gateway_config.json, loading Cognito configuration")
        with config_path.open("r") as f:
            existing_config = json.load(f)

    if existing_config and "cognito_response" in existing_config:
        logger.info("Step 1: Reusing existing Cognito OAuth configuration")
        cognito_response = existing_config["cognito_response"]
    else:
        logger.info("Step 1: Creating new OAuth authorizer with Cognito")
        cognito_response = setup.create_oauth_with_cognito("AgentGateway")

    logger.info("Step 2: Getting or creating MCP Gateway")
    gateway = setup.get_or_create_gateway(
        authorizer_config=cognito_response["authorizer_config"], name="AgentGateway"
    )

    logger.info("Step 3: Getting or creating Lambda target")
    
    lambda_config_path = Path("lambda_config.json")
    lambda_arn = None
    tool_schema = None
    
    if lambda_config_path.exists():
        logger.info("Found lambda_config.json, using custom Lambda")
        with lambda_config_path.open() as f:
            lambda_config = json.load(f)
        lambda_arn = lambda_config.get("lambda_arn")
        tool_schema = lambda_config.get("tool_schema")
    
    if lambda_arn and tool_schema:
        logger.info(f"Using custom Lambda: {lambda_arn}")
        lambda_target = setup.get_or_create_lambda_target(
            gateway, name="AgentTools", lambda_arn=lambda_arn, tool_schema=tool_schema
        )
    else:
        logger.info("Using demo Lambda (auto-generated)")
        lambda_target = setup.get_or_create_lambda_target(gateway, name="DemoTools")

    config = {
        "region": setup.region,
        "gateway_id": gateway["gatewayId"],
        "gateway_url": gateway["gatewayUrl"],
        "cognito_response": cognito_response,
        "client_info": cognito_response.get("client_info"),
        "lambda_target_arn": lambda_target.get("arn"),
    }

    config_path = Path("gateway_config.json")
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"Gateway configuration saved to: {config_path}")
    logger.info("=" * 60)
    logger.info("Gateway Setup Complete!")
    logger.info(f"Gateway ID: {gateway['gatewayId']}")
    logger.info(f"Gateway URL: {gateway['gatewayUrl']}")
    logger.info("Cognito configured successfully")
    logger.info("=" * 60)

    logger.info("Getting test access token...")
    access_token = setup.get_access_token(cognito_response["client_info"])
    logger.info(f"Access Token (first 50 chars): {access_token[:50]}...")

    logger.info("\nNext steps:")
    logger.info("1. Use the gateway_config.json for your agent configuration")
    logger.info("2. Create custom Lambda functions with your tools")
    logger.info("3. Add them as targets to the gateway")
    logger.info("4. Test with different user tokens")


if __name__ == "__main__":
    main()
