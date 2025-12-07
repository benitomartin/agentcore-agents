from bedrock_agentcore.memory.session import MemorySession, MemorySessionManager
from loguru import logger


class AgentSessionManager:
    def __init__(self, memory_id: str, region: str = "eu-central-1") -> None:
        self.memory_id = memory_id
        self.region = region
        self.manager = MemorySessionManager(memory_id=memory_id, region_name=region)
        logger.info(f"SessionManager initialized for memory: {memory_id}")

    def get_or_create_session(self, actor_id: str, session_id: str) -> MemorySession:
        logger.info(f"Getting or creating session for actor: {actor_id}, session: {session_id}")
        session = self.manager.create_memory_session(actor_id=actor_id, session_id=session_id)
        logger.info(f"Session ready: {session}")
        return session

    def get_session(self, actor_id: str, session_id: str) -> MemorySession:
        logger.info(f"Getting session for actor: {actor_id}, session: {session_id}")
        session = self.manager.get_memory_session(actor_id=actor_id, session_id=session_id)
        return session
