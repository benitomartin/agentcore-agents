#!/usr/bin/env python3
"""Add required IAM permissions to AgentCore Runtime execution role."""

import json
import sys

import boto3
from loguru import logger

from agentcore_agents.config import settings


def add_runtime_permissions(role_name: str) -> None:
    """Add required IAM permissions to the execution role."""
    iam = boto3.client("iam", region_name=settings.aws.region)

    # Gateway permissions
    gateway_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:ListGateways",
                    "bedrock-agentcore:GetGateway",
                ],
                "Resource": "*",
            }
        ],
    }

    # Memory permissions - using wildcard as some AgentCore actions require it
    memory_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:ListMemories",
                    "bedrock-agentcore:GetMemory",
                    "bedrock-agentcore:CreateMemory",
                    "bedrock-agentcore:ListSessions",
                    "bedrock-agentcore:GetSession",
                    "bedrock-agentcore:CreateSession",
                    "bedrock-agentcore:PutEvents",
                ],
                "Resource": "*",
            }
        ],
    }

    try:
        # Add Gateway permissions
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="AgentCoreGatewayAccess",
            PolicyDocument=json.dumps(gateway_policy),
        )
        logger.info(f"✓ Added Gateway permissions to role: {role_name}")

        # Add Memory permissions
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="AgentCoreMemoryAccess",
            PolicyDocument=json.dumps(memory_policy),
        )
        logger.info(f"✓ Added Memory permissions to role: {role_name}")

        logger.info("✓ All permissions added successfully!")
    except Exception as e:
        logger.error(f"Failed to add permissions: {e}")
        sys.exit(1)


def main() -> None:
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Add IAM permissions to AgentCore Runtime execution role")
    parser.add_argument(
        "--role-name",
        type=str,
        help="IAM role name (e.g., AmazonBedrockAgentCoreSDKRuntime-eu-central-1-xxx)",
    )
    args = parser.parse_args()

    if args.role_name:
        role_name = args.role_name
    else:
        try:
            import yaml
            with open(".bedrock_agentcore.yaml") as f:
                config = yaml.safe_load(f)
                default_agent = config.get("default_agent")
                agent_config = config.get("agents", {}).get(default_agent, {})
                execution_role_arn = agent_config.get("aws", {}).get("execution_role", "")
                if execution_role_arn:
                    role_name = execution_role_arn.split("/")[-1]
                    logger.info(f"Found execution role from config: {role_name}")
                else:
                    logger.error("No execution role found in .bedrock_agentcore.yaml")
                    sys.exit(1)
        except Exception as e:
            logger.error(f"Could not read config: {e}")
            logger.info("Please specify --role-name")
            sys.exit(1)

    add_runtime_permissions(role_name)


if __name__ == "__main__":
    main()

