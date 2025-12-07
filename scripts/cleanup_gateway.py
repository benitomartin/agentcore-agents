import json
from pathlib import Path

from loguru import logger

from agentcore_agents.gateway.setup import GatewaySetup


def main() -> None:
    logger.info("Starting Gateway cleanup")

    config_path = Path("gateway_config.json")
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        logger.info("Nothing to clean up")
        return

    with config_path.open() as f:
        config = json.load(f)

    setup = GatewaySetup(region=config["region"])

    logger.info(f"Cleaning up gateway: {config['gateway_id']}")
    setup.cleanup_gateway(config["gateway_id"], config["client_info"])

    config_path.unlink()
    logger.info(f"Deleted config file: {config_path}")

    logger.info("Gateway cleanup completed successfully")


if __name__ == "__main__":
    main()
