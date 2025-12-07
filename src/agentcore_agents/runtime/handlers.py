from typing import Any

from loguru import logger

from agentcore_agents.agent import StrandsAgentWrapper
from agentcore_agents.config import settings
from agentcore_agents.runtime.app import app


@app.entrypoint
def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    logger.info(f"Runtime received payload: {payload}")

    prompt = payload.get("prompt", "")
    actor_id = payload.get("actor_id", settings.memory.actor_id)
    session_id = payload.get("session_id", settings.memory.session_id)

    logger.info(f"Creating new agent for {actor_id}:{session_id}")
    agent = StrandsAgentWrapper(actor_id=actor_id, session_id=session_id)

    response = agent.run(prompt)
    return response


if __name__ == "__main__":
    app.run()
