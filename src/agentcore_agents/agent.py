from typing import Any

from loguru import logger
from strands import Agent
from strands.models import BedrockModel

from agentcore_agents.config import settings
from agentcore_agents.memory.hooks import MemoryHookProvider
from agentcore_agents.memory.manager import AgentMemoryManager
from agentcore_agents.memory.session import AgentSessionManager
from agentcore_agents.prompts.system import SYSTEM_PROMPT
from agentcore_agents.tools.registry import TOOLS


class StrandsAgentWrapper:
    def __init__(
        self,
        actor_id: str | None = None,
        session_id: str | None = None,
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

        session_manager = AgentSessionManager(memory_id=memory.id, region=settings.aws.region)
        memory_session = session_manager.get_or_create_session(
            actor_id=actor_id, session_id=session_id
        )

        memory_hook = MemoryHookProvider(
            memory_session=memory_session, actor_id=actor_id, session_id=session_id
        )

        self.agent = Agent(
            model=model,
            tools=TOOLS,
            hooks=[memory_hook],
            system_prompt=SYSTEM_PROMPT,
        )

    def run(self, prompt: str) -> dict[str, Any]:
        logger.info(f"Processing prompt: {prompt}")
        result = self.agent(prompt)
        response = {"prompt": prompt, "response": result.message}
        return response
