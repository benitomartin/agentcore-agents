from loguru import logger

from agentcore_agents.browser.setup import get_browser_tool
from agentcore_agents.config import settings


def main() -> None:
    logger.info("Setting up AgentCore Browser Tool")
    logger.info("=" * 60)

    logger.info(f"Region: {settings.aws.region}")

    logger.info("\nCreating/verifying browser tool...")
    try:
        browser_tool = get_browser_tool()
        logger.info("✓ Browser tool ready")
        logger.info(f"  Tool type: {type(browser_tool).__name__}")
        logger.info("=" * 60)
        logger.info("Browser setup complete!")
        logger.info("\nNext steps:")
        logger.info("1. Run tests/test_browser.py to test the browser")
        logger.info("2. Use the browser tool in your agent via tools registry")
        logger.info("3. Check AWS Console > AgentCore > Built-in tools to see your browser")
    except Exception as e:
        logger.error(f"Error setting up browser: {e}")
        logger.info("\nTroubleshooting:")
        logger.info("1. Verify IAM permissions for AgentCore Browser")
        logger.info("2. Check AWS region is supported for AgentCore")
        logger.info("3. Ensure AWS credentials are configured")
        raise


if __name__ == "__main__":
    main()
