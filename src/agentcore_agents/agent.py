from typing import Any

from loguru import logger
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient

from agentcore_agents.config import settings
from agentcore_agents.memory.hooks import MemoryHookProvider
from agentcore_agents.memory.manager import AgentMemoryManager
from agentcore_agents.memory.session import AgentSessionManager
from agentcore_agents.prompts.system import SYSTEM_PROMPT


class StrandsAgentWrapper:
    def __init__(
        self,
        actor_id: str | None = None,
        session_id: str | None = None,
        use_gateway: bool = False,
        gateway_url: str | None = None,
        access_token: str | None = None,
    ) -> None:
        actor_id = actor_id or settings.memory.actor_id
        session_id = session_id or settings.memory.session_id

        logger.info(f"Agent initialized with model: {settings.model.model_id}")

        model = BedrockModel(
            model_id=settings.model.model_id,
            region_name=settings.aws.region,
            max_tokens=settings.model.max_tokens,
            temperature=settings.model.temperature,
        )

        memory_manager = AgentMemoryManager(region=settings.aws.region)
        memory = memory_manager.get_or_create_memory(
            name=settings.memory.name,
            description=settings.memory.description,
            event_expiry_days=settings.memory.event_expiry_days,
        )

        memory_id = getattr(memory, "id", "")
        session_manager = AgentSessionManager(memory_id=memory_id, region=settings.aws.region)
        memory_session = session_manager.get_or_create_session(
            actor_id=actor_id, session_id=session_id
        )

        memory_hook = MemoryHookProvider(
            memory_session=memory_session, actor_id=actor_id, session_id=session_id
        )

        if use_gateway:
            if not gateway_url or not access_token:
                raise ValueError("gateway_url and access_token are required when use_gateway=True")

            logger.info("Connecting to Gateway to get tools...")
            self.mcp_client = MCPClient(
                lambda: streamablehttp_client(
                    gateway_url, headers={"Authorization": f"Bearer {access_token}"}
                )
            )
            self.mcp_client.__enter__()
            tools = self.mcp_client.list_tools_sync()
            logger.info(f"Found {len(tools)} tools from Gateway")
        else:
            raise ValueError(
                "use_gateway=True is required. Local tools have been removed. "
                "Please use Gateway tools by setting use_gateway=True and "
                "providing gateway_url and access_token."
        )

        self.agent = Agent(
            model=model,
            tools=tools,
            hooks=[memory_hook],
            system_prompt=SYSTEM_PROMPT,
        )

    def run(self, prompt: str) -> dict[str, Any]:
        logger.info(f"Processing prompt: {prompt}")
        result = self.agent(prompt)
        response = {"prompt": prompt, "response": result.message}
        return response

    def __enter__(self) -> "StrandsAgentWrapper":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.mcp_client:
            self.mcp_client.__exit__(exc_type, exc_val, exc_tb)
