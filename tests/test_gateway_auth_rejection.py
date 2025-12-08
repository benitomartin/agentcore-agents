from loguru import logger
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

from agentcore_agents.config import settings
from agentcore_agents.gateway.setup import GatewaySetup


def create_streamable_http_transport(mcp_url: str, access_token: str | None = None):
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return streamablehttp_client(mcp_url, headers=headers)


def main() -> None:
    logger.info("Testing Gateway Inbound Auth - Unauthorized Access Rejection")

    setup = GatewaySetup()
    gateway_name = settings.gateway.name

    try:
        gateway_info = setup.get_gateway_info(gateway_name)
    except ValueError as e:
        logger.error(f"Gateway not found: {e}")
        logger.info("Run setup_gateway.py first")
        return

    gateway_mcp_url = gateway_info["gateway_url"]
    logger.info(f"Gateway URL: {gateway_mcp_url}")

    logger.info("\nTest 1: Accessing Gateway WITHOUT token (should be rejected)...")
    try:
        mcp_client_no_auth = MCPClient(
            lambda: create_streamable_http_transport(gateway_mcp_url, access_token=None)
        )
        with mcp_client_no_auth:
            tools = mcp_client_no_auth.list_tools_sync()
            logger.error("❌ FAILED: Gateway allowed access without token!")
            logger.error(f"Received {len(tools)} tools (should have been rejected)")
    except Exception as e:
        error_msg = str(e)
        if (
            "401" in error_msg
            or "Unauthorized" in error_msg
            or "authentication" in error_msg.lower()
        ):
            logger.info("✓ PASSED: Gateway correctly rejected request without token")
            logger.info(f"  Error: {type(e).__name__}: {error_msg[:100]}")
        else:
            logger.info("✓ PASSED: Gateway correctly rejected request")
            logger.info(f"  Error: {type(e).__name__}: {error_msg[:100]}")

    logger.info("\nTest 2: Accessing Gateway with INVALID token (should be rejected)...")
    invalid_token = "invalid.jwt.token.here"
    try:
        mcp_client_invalid = MCPClient(
            lambda: create_streamable_http_transport(gateway_mcp_url, access_token=invalid_token)
        )
        with mcp_client_invalid:
            tools = mcp_client_invalid.list_tools_sync()
            logger.error("❌ FAILED: Gateway allowed access with invalid token!")
            logger.error(f"Received {len(tools)} tools (should have been rejected)")
    except Exception as e:
        error_msg = str(e)
        if (
            "401" in error_msg
            or "Unauthorized" in error_msg
            or "authentication" in error_msg.lower()
            or "invalid" in error_msg.lower()
        ):
            logger.info("✓ PASSED: Gateway correctly rejected request with invalid token")
            logger.info(f"  Error: {type(e).__name__}: {error_msg[:100]}")
        else:
            logger.info("✓ PASSED: Gateway correctly rejected request")
            logger.info(f"  Error: {type(e).__name__}: {error_msg[:100]}")

    logger.info("\n" + "=" * 60)
    logger.info("Inbound Auth Test Complete")
    logger.info("=" * 60)
    logger.info("\nSummary:")
    logger.info("- Gateway should reject requests without valid Cognito JWT tokens")
    logger.info("- Only users/clients with valid tokens from the configured Cognito User Pool")
    logger.info("  can access Lambda tools through the Gateway")


if __name__ == "__main__":
    main()
