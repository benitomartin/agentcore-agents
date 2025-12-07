from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
from loguru import logger

from agentcore_agents.config import settings


class GatewaySetup:
    def __init__(self, region: str | None = None) -> None:
        self.region = region or settings.aws.region
        self.client = GatewayClient(region_name=self.region)
        logger.info(f"GatewaySetup initialized for region: {self.region}")

    def create_oauth_with_cognito(self, gateway_name: str = "AgentGateway") -> dict:
        logger.info(f"Creating OAuth authorizer with Cognito for gateway: {gateway_name}")
        cognito_response = self.client.create_oauth_authorizer_with_cognito(gateway_name)
        logger.info(f"Cognito setup completed: {list(cognito_response.keys())}")
        return cognito_response

    def get_or_create_gateway(self, authorizer_config: dict, name: str | None = None) -> dict:
        existing = self._find_gateway_by_name(name)
        if existing:
            gateway_id = existing.get("gatewayId") or existing.get("id")
            logger.info(f"Gateway '{name}' already exists with ID: {gateway_id}")
            return existing

        logger.info("Creating MCP Gateway")
        gateway = self.client.create_mcp_gateway(
            name=name,
            role_arn=None,
            authorizer_config=authorizer_config,
            enable_semantic_search=True,
        )
        logger.info(f"Gateway created: {gateway['gatewayId']}")

        logger.info("Fixing IAM permissions for gateway")
        self.client.fix_iam_permissions(gateway)

        return gateway

    def _find_gateway_by_name(self, name: str | None) -> dict | None:
        if not name:
            return None

        gateways = self.client.list_gateways()
        gateway_list = gateways.get("items", [])

        for gateway in gateway_list:
            if gateway.get("name") == name:
                gateway_id = gateway.get("gatewayId")
                logger.info(f"Found existing gateway '{name}' with ID: {gateway_id}")
                response = self.client.get_gateway(gateway_id)
                return response.get("gateway", response)
        return None

    def get_or_create_lambda_target(self, gateway: dict, name: str | None = None) -> dict:
        existing = self._find_target_by_name(gateway, name)
        if existing:
            logger.info(f"Lambda target '{name}' already exists: {existing.get('arn', 'unknown')}")
            return existing

        logger.info(f"Creating Lambda target for gateway: {gateway['gatewayId']}")
        lambda_target = self.client.create_mcp_gateway_target(
            gateway=gateway,
            name=name,
            target_type="lambda",
            target_payload=None,
            credentials=None,
        )
        logger.info(f"Lambda target created: {lambda_target.get('arn', 'unknown')}")
        return lambda_target

    def _find_target_by_name(self, gateway: dict, name: str | None) -> dict | None:
        if not name:
            return None

        targets = self.client.list_gateway_targets(gateway["gatewayId"])
        target_list = targets.get("items", [])

        for target in target_list:
            if target.get("name") == name:
                logger.info(f"Found existing target '{name}' in gateway")
                return target
        return None

    def get_access_token(self, client_info: dict) -> str:
        logger.info("Getting OAuth access token from Cognito")
        access_token = self.client.get_access_token_for_cognito(client_info)
        logger.info("Access token obtained successfully")
        return access_token

    def cleanup_gateway(self, gateway_id: str, client_info: dict) -> None:
        logger.info(f"Cleaning up gateway: {gateway_id}")
        self.client.cleanup_gateway(gateway_id, client_info)
        logger.info("Gateway cleanup completed")
