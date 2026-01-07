import os

from loguru import logger

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
    if not user_access_token:
        logger.error("Failed to get user access token")
        return

    user_identity = extract_user_identity(user_access_token)
    actor_id = user_identity["actor_id"]
    session_id = settings.memory.session_id

    gateway_mcp_url = gateway_info["gateway_url"]

    with StrandsAgentWrapper(
        actor_id=actor_id,
        session_id=session_id,
        use_gateway=True,
        gateway_url=gateway_mcp_url,
        access_token=user_access_token,
    ) as agent:
        # test_prompt = "Can you check the documents in the S3 Bucket?"
        # response = agent.run(test_prompt)
        # logger.info(f"Agent response: {response['response']['content'][0]['text']}")
        
        # follow_up = "Can you read the content of the file?"
        # response2 = agent.run(follow_up)
        # logger.info(f"Agent response: {response2['response']['content'][0]['text']}")

        follow_up = "Can you summarize the conversation so far?"
        response3 = agent.run(follow_up)
        logger.info(f"Agent response: {response3['response']['content'][0]['text']}")

if __name__ == "__main__":
    main()
