import json
from pathlib import Path

from loguru import logger
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient

from agentcore_agents.config import settings
from agentcore_agents.gateway.setup import GatewaySetup


def create_streamable_http_transport(mcp_url: str, access_token: str):
    return streamablehttp_client(mcp_url, headers={"Authorization": f"Bearer {access_token}"})


def main() -> None:
    logger.info("Testing Gateway with MCP")

    config_path = Path("gateway_config.json")
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        logger.info("Run setup_gateway.py first")
        return

    with config_path.open() as f:
        config = json.load(f)

    logger.info(f"Gateway URL: {config['gateway_url']}")

    setup = GatewaySetup(region=config["region"])
    logger.info("Getting OAuth access token...")
    access_token = setup.get_access_token(config["client_info"])
    logger.info(f"Access token obtained (first 50 chars): {access_token[:50]}...")

    gateway_mcp_url = config["gateway_url"]
    logger.info(f"MCP URL: {gateway_mcp_url}")

    logger.info("Connecting to Gateway via MCP...")
    mcp_client = MCPClient(lambda: create_streamable_http_transport(gateway_mcp_url, access_token))

    with mcp_client:
        logger.info("Listing available tools from Gateway...")
        tools = mcp_client.list_tools_sync()

        logger.info(f"Found {len(tools)} tools:")
        for tool in tools:
            logger.info(
                f"  - {tool.tool_name}: {tool.tool_spec.get('description', 'no description')}"
            )

        if not tools:
            logger.warning("No tools found in Gateway. The demo Lambda may not have tools yet.")
            return

        logger.info("\nCreating agent with Gateway tools...")
        agent = Agent(
            model=BedrockModel(
                model_id=settings.model.model_id,
                region_name=settings.aws.region,
                max_tokens=settings.model.max_tokens,
            ),
            tools=tools,
        )

        logger.info("\nTesting agent with a simple prompt...")
        test_prompt = "Can you give me the time?"
        logger.info(f"Prompt: {test_prompt}")

        response = agent(test_prompt)
        logger.info(f"\nAgent response:\n{response.message['content'][0]['text']}")

        logger.info("\n✓ Gateway test successful!")


if __name__ == "__main__":
    main()
