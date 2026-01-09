# Deployment Guide

Simple step-by-step guide to deploy and test the AgentCore agent.

## Prerequisites

- AWS credentials configured (`aws configure`)
- Environment variables in `.env` file
- Dependencies installed: `uv sync`

## Deployment Steps

### 1. Create S3 Bucket

```bash
make agentcore-s3-setup
```

Creates the S3 bucket for storing documents that the agent can read.

### 2. Deploy Lambda Function

```bash
make agentcore-lambda-deploy
```

Deploys the Lambda function containing Gateway tools (calculator, get_current_time, read_s3_document).

### 3. Setup Gateway and Cognito

```bash
make agentcore-gateway
```

Creates:
- AgentCore Gateway
- Cognito User Pool
- Cognito OAuth Client
- Associates Lambda with Gateway

### 4. Setup Test User

```bash
uv run scripts/setup_user_auth.py
```

Creates a test user in Cognito for authentication.

### 5. Configure and Deploy Agent

```bash
uv run agentcore configure
```

Follow prompts to configure the agent. Then deploy:

```bash
uv run agentcore deploy
```

### 6. Add Runtime Permissions

```bash
uv run scripts/setup_runtime_permissions.py
```

Adds required IAM permissions for Gateway and Memory access.

## Testing

### Test Locally

```bash
uv run tests/test_agent_with_user_identity.py
```

Tests:
- User authentication with Cognito
- Gateway tool discovery
- Tool execution (S3 document reading)
- Memory persistence
- Multi-turn conversations

### Test Deployed Agent

```bash
TOKEN=$(uv run python -c "
from agentcore_agents.auth.cognito import get_user_token
from agentcore_agents.auth.secrets_manager import get_client_secret
from agentcore_agents.gateway.setup import GatewaySetup
from agentcore_agents.config import settings

setup = GatewaySetup()
client_info = setup.get_client_info_from_gateway()
client_secret = get_client_secret(settings.gateway.name, setup.region)
token_data = get_user_token(
    client_info['client_id'],
    client_secret,
    'testuser',
    'TestPassword123!'
)
print(token_data['access_token'])
")

agentcore invoke '{"prompt": "Can you tell me how many documents are in the S3 bucket?"}' --bearer-token "$TOKEN"
```

## Cleanup

Do not forget to delete all created ressources.

**Note:** This does NOT delete the cognito user pool, S3 bucket, or deployed agent. Delete those manually via AWS Console or CLI if needed.

## Environment Variables

Optional test user credentials (defaults provided):
- `COGNITO_TEST_USERNAME` (default: `testuser`)
- `COGNITO_TEST_PASSWORD` (default: `TestPassword123!`)
- `COGNITO_TEST_EMAIL` (default: `testuser@example.com`)

