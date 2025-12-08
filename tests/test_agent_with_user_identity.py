import os
import uuid
from typing import Any

from loguru import logger
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient

from agentcore_agents.agent import StrandsAgentWrapper
from agentcore_agents.auth.cognito import (
    create_cognito_user,
    get_user_token,
    update_cognito_client_for_user_auth,
)
from agentcore_agents.auth.secrets_manager import get_client_secret
from agentcore_agents.auth.user_identity import extract_user_identity
from agentcore_agents.config import settings
from agentcore_agents.gateway.setup import GatewaySetup


def create_streamable_http_transport(mcp_url: str, access_token: str) -> Any:
    return streamablehttp_client(mcp_url, headers={"Authorization": f"Bearer {access_token}"})


def main() -> None:
    setup = GatewaySetup()
    gateway_name = settings.gateway.name

    try:
        gateway_info = setup.get_gateway_info(gateway_name)
        client_info = setup.get_client_info_from_gateway(gateway_name)
    except ValueError as e:
        logger.error(f"Gateway not found: {e}")
        return

    user_pool_id = client_info["user_pool_id"]
    client_id = client_info["client_id"]
    client_secret = get_client_secret(gateway_name, setup.region)

    username = os.getenv("COGNITO_TEST_USERNAME", "testuser")
    password = os.getenv("COGNITO_TEST_PASSWORD", "TestPassword123!")
    email = os.getenv("COGNITO_TEST_EMAIL", "testuser@example.com")

    update_cognito_client_for_user_auth(user_pool_id, client_id)
    create_cognito_user(user_pool_id, username, password, email)

    token_data = get_user_token(client_id, client_secret, username, password)
    user_access_token = token_data.get("access_token")

    user_identity = extract_user_identity(user_access_token)
    actor_id = user_identity["actor_id"]
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    gateway_mcp_url = gateway_info["gateway_url"]
    mcp_client = MCPClient(
        lambda: create_streamable_http_transport(gateway_mcp_url, user_access_token)
    )

    with mcp_client:
        tools = mcp_client.list_tools_sync()

        StrandsAgentWrapper(actor_id=actor_id, session_id=session_id)

        gateway_agent = Agent(
            model=BedrockModel(
                model_id=settings.model.model_id,
                region_name=settings.aws.region,
                max_tokens=settings.model.max_tokens,
            ),
            tools=tools,
        )

        test_prompt = "Can you check the documents in the S3 Bucket?"
        response = gateway_agent(test_prompt)
        logger.info(f"Agent response: {response.message['content'][0]['text']}")

        follow_up = "Can you read the content of the file?"
        response2 = gateway_agent(follow_up)
        logger.info(f"Agent response: {response2.message['content'][0]['text']}")


if __name__ == "__main__":
    main()
