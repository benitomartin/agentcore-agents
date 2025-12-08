import json
from pathlib import Path

import boto3
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
from botocore.exceptions import ClientError
from loguru import logger

from agentcore_agents.auth.secrets_manager import get_client_secret
from agentcore_agents.config import settings


class GatewaySetup:
    def __init__(self, region: str | None = None) -> None:
        self.region = region or settings.aws.region
        self.client = GatewayClient(region_name=self.region)
        if not hasattr(self.client, "logger"):
            self.client.logger = logger
        logger.info(f"GatewaySetup initialized for region: {self.region}")

    def create_oauth_with_cognito(self, gateway_name: str | None = None) -> dict:
        if gateway_name is None:
            gateway_name = settings.gateway.name
        logger.info(f"Creating OAuth authorizer with Cognito for gateway: {gateway_name}")
        cognito_response = self.client.create_oauth_authorizer_with_cognito(gateway_name)
        logger.info(f"Cognito setup completed: {list(cognito_response.keys())}")
        return cognito_response

    def get_or_create_gateway(self, authorizer_config: dict, name: str | None = None) -> dict:
        existing = self._find_gateway_by_name(name)
        if existing:
            gateway_id = existing.get("gatewayId") or existing.get("id")
            logger.info(f"Gateway '{name}' already exists with ID: {gateway_id}")

            existing_auth = existing.get("authorizerConfiguration", {})
            if existing_auth:
                logger.info("✓ Gateway has inbound auth configured")
            else:
                logger.warning("⚠️ Gateway exists but may not have inbound auth configured")
                logger.warning("  Delete and recreate the gateway to apply inbound auth")

            return existing

        logger.info("Creating MCP Gateway with Inbound Auth")
        logger.info("  - JWT validation via Cognito User Pool")
        gateway = self.client.create_mcp_gateway(
            name=name,
            role_arn=None,
            authorizer_config=authorizer_config,
            enable_semantic_search=True,
        )
        logger.info(f"Gateway created: {gateway['gatewayId']}")
        logger.info("✓ Inbound auth configured successfully")

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

    def get_or_create_lambda_target(
        self,
        gateway: dict,
        name: str,
        lambda_arn: str,
        tool_schema: dict,
    ) -> dict:
        existing = self._find_target_by_name(gateway, name)
        if existing:
            logger.info(f"Lambda target '{name}' already exists: {existing.get('arn', 'unknown')}")
            return existing

        logger.info(f"Creating Lambda target for gateway: {gateway['gatewayId']}")

        target_payload = {
            "lambdaArn": lambda_arn,
            "toolSchema": tool_schema,
        }
        logger.info(f"Using Lambda: {lambda_arn}")

        lambda_target = self.client.create_mcp_gateway_target(
            gateway=gateway,
            name=name,
            target_type="lambda",
            target_payload=target_payload,
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

    def get_access_token(self, client_info: dict, gateway_name: str | None = None) -> str:
        if gateway_name is None:
            gateway_name = settings.gateway.name
        logger.info("Getting OAuth access token from Cognito")

        client_info_with_secret = client_info.copy()
        if "client_secret" not in client_info_with_secret:
            logger.info("Retrieving client secret from Secrets Manager...")
            client_secret = get_client_secret(gateway_name, self.region)
            client_info_with_secret["client_secret"] = client_secret

        access_token = self.client.get_access_token_for_cognito(client_info_with_secret)
        logger.info("Access token obtained successfully")
        return access_token

    def get_gateway_info(self, gateway_name: str | None = None) -> dict:
        if gateway_name is None:
            gateway_name = settings.gateway.name
        gateway = self._find_gateway_by_name(gateway_name)
        if not gateway:
            raise ValueError(f"Gateway '{gateway_name}' not found")

        return {
            "gateway_id": gateway.get("gatewayId"),
            "gateway_url": gateway.get("gatewayUrl"),
            "gateway_name": gateway.get("name", gateway_name),
            "region": self.region,
        }

    def get_client_info_from_gateway(self, gateway_name: str | None = None) -> dict:
        if gateway_name is None:
            gateway_name = settings.gateway.name
        gateway = self._find_gateway_by_name(gateway_name)
        if not gateway:
            raise ValueError(f"Gateway '{gateway_name}' not found")

        authorizer_config = gateway.get("authorizerConfiguration", {})
        if not authorizer_config:
            return self._get_client_info_from_cognito()

        custom_jwt = authorizer_config.get("customJWTAuthorizer", {})
        if not custom_jwt:
            custom_jwt = authorizer_config

        issuer = custom_jwt.get("issuer", "")
        audience = custom_jwt.get("audience", "")

        discovery_url = custom_jwt.get("discoveryUrl", "")
        allowed_clients = custom_jwt.get("allowedClients", [])

        if discovery_url and not issuer:
            issuer = discovery_url.replace("/.well-known/openid-configuration", "")

        if allowed_clients and not audience:
            audience = allowed_clients[0] if isinstance(allowed_clients, list) else allowed_clients

        jwks_uri = custom_jwt.get("jwksUri", "")
        if jwks_uri and not issuer:
            issuer = jwks_uri.replace("/.well-known/jwks.json", "")

        if not issuer:
            return self._get_client_info_from_cognito()
        if not audience:
            raise ValueError("Audience not found in authorizer config")

        user_pool_id = issuer.split("/")[-1] if "/" in issuer else issuer
        client_id = audience

        if not user_pool_id:
            raise ValueError(f"Could not extract user_pool_id from issuer: {issuer}")

        return {
            "user_pool_id": user_pool_id,
            "client_id": client_id,
        }

    def _get_client_info_from_cognito(self) -> dict:
        cognito_client = boto3.client("cognito-idp", region_name=self.region)

        user_pool_id = settings.cognito.user_pool_id
        if not user_pool_id:
            raise ValueError(
                "Cannot get client info: Gateway has no authorizer config and "
                "COGNITO__USER_POOL_ID not set in environment"
            )

        try:
            response = cognito_client.list_user_pool_clients(UserPoolId=user_pool_id, MaxResults=10)
            clients = response.get("UserPoolClients", [])

            if not clients:
                raise ValueError(f"No app clients found in user pool: {user_pool_id}")

            client_id = clients[0].get("ClientId")
            if not client_id:
                raise ValueError("Could not extract client_id from Cognito")

            return {
                "user_pool_id": user_pool_id,
                "client_id": client_id,
            }
        except ClientError as e:
            raise ValueError(f"Failed to get client info from Cognito: {e}") from e

    def get_lambda_arn(self, function_name: str | None = None) -> str:
        if function_name is None:
            function_name = settings.lambda_settings.function_name

        lambda_client = boto3.client("lambda", region_name=self.region)
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            lambda_arn = response["Configuration"]["FunctionArn"]
            logger.info(f"Retrieved Lambda ARN: {lambda_arn}")
            return lambda_arn
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                raise ValueError(
                    f"Lambda function '{function_name}' not found. Run deploy_lambda.py first."
                ) from e
            raise

    def load_tool_schema(self) -> dict:
        schema_path = Path("src/agentcore_agents/lambda/tool_schema.json")
        if not schema_path.exists():
            raise FileNotFoundError(f"Tool schema not found: {schema_path}")

        with schema_path.open() as f:
            schema_data = json.load(f)

        return {
            "inlinePayload": [
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "inputSchema": tool["inputSchema"],
                }
                for tool in schema_data["tools"]
            ]
        }

    def cleanup_gateway(self, gateway_id: str, client_info: dict) -> None:
        logger.info(f"Cleaning up gateway: {gateway_id}")
        self.client.cleanup_gateway(gateway_id, client_info)
        logger.info("Gateway cleanup completed")
