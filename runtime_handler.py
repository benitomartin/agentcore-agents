import sys
from pathlib import Path
from typing import Any

from loguru import logger

# Add src directory to Python path so agentcore_agents can be imported
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from agentcore_agents.agent import StrandsAgentWrapper
from agentcore_agents.auth.user_identity import extract_user_identity
from agentcore_agents.config import settings
from agentcore_agents.gateway.setup import GatewaySetup
from bedrock_agentcore.runtime.app import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        prompt = payload.get("prompt", "")
        
        # Get bearer token from request headers
        bearer_token = None
        if hasattr(context, "request_headers") and isinstance(context.request_headers, dict):
            auth_header = (
                context.request_headers.get("Authorization")
                or context.request_headers.get("authorization")
            )
            if auth_header and isinstance(auth_header, str) and auth_header.startswith("Bearer "):
                bearer_token = auth_header[7:]
        
        if not bearer_token:
            bearer_token = payload.get("bearer_token") or payload.get("access_token")
        
        if not bearer_token:
            logger.error("No bearer token found in request")
            return {"error": "Authentication required. Please provide a bearer token"}
        
        logger.info("Bearer token found, proceeding with agent creation")
        
        # Extract user identity from token (same as test files)
        user_identity = extract_user_identity(bearer_token)
        actor_id = user_identity["actor_id"]
        session_id = payload.get("session_id") or settings.memory.session_id

        logger.info(f"Creating agent for actor_id={actor_id}, session_id={session_id}")

        # Get Gateway URL - try from config/env first, then query API, then fallback
        gateway_mcp_url = settings.gateway.gateway_url
        
        if not gateway_mcp_url:
            try:
                setup = GatewaySetup()
                gateway_info = setup.get_gateway_info(settings.gateway.name)
                gateway_mcp_url = gateway_info["gateway_url"]
                logger.info(f"Retrieved Gateway URL from API: {gateway_mcp_url}")
            except Exception as e:
                logger.warning(f"Could not get Gateway URL from API: {e}")
                gateway_mcp_url = "https://agentgateway-3sqyxtamyl.gateway.bedrock-agentcore.eu-central-1.amazonaws.com/mcp"
                logger.info(f"Using fallback Gateway URL: {gateway_mcp_url}")
        
        if not gateway_mcp_url:
            return {"error": "Gateway URL not configured"}

        # Use same token for Gateway access (same as test files)
        with StrandsAgentWrapper(
            actor_id=actor_id,
            session_id=session_id,
            use_gateway=True,
            gateway_url=gateway_mcp_url,
            access_token=bearer_token,  # Same token from user
        ) as agent:
            response = agent.run(prompt)
            return response
    except Exception as e:
        logger.error(f"Error in invoke handler: {e}", exc_info=True)
        return {"error": f"Handler error: {str(e)}"}


if __name__ == "__main__":
    logger.info("Starting BedrockAgentCoreApp runtime server...")
    logger.info("Note: This is designed for AWS AgentCore Runtime deployment.")
    app.run()

