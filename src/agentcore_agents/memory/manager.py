from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager
from loguru import logger


class AgentMemoryManager:
    def __init__(self, region: str = "eu-central-1") -> None:
        self.region = region
        self.manager = MemoryManager(region_name=region)
        logger.info(f"MemoryManager initialized for region: {region}")

    def get_or_create_memory(
        self, name: str, description: str = "", event_expiry_days: int = 30
    ) -> object:
        logger.info(f"Getting or creating memory: {name}")
        memory = self.manager.get_or_create_memory(
            name=name, 
            strategies=[], 
            description=description, 
            event_expiry_days=event_expiry_days
        )
        logger.info(f"Memory ID: {memory.id}")
        return memory
