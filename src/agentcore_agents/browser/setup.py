from loguru import logger
from strands_tools.browser import AgentCoreBrowser

from agentcore_agents.config import settings


def get_browser_tool() -> AgentCoreBrowser:
    logger.info("Creating AgentCore Browser tool")
    logger.info(f"Region: {settings.aws.region}")
    browser_tool = AgentCoreBrowser(region=settings.aws.region)
    logger.info("Browser tool created successfully")
    return browser_tool
