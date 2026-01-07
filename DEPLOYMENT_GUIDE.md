# Deployment Guide

Simple step-by-step guide to deploy and test the AgentCore Gateway setup.

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

## Testing

### Run Gateway Test with User Identity

```bash
uv run tests/test_agent_with_user_identity.py
```

Tests:
- User authentication with Cognito
- Gateway tool discovery
- Tool execution (S3 document reading)
- Memory persistence
- Multi-turn conversations

### Run Authentication Rejection Test

```bash
uv run tests/test_gateway_auth_rejection.py
```

Verifies that Gateway correctly rejects unauthorized access.

## Cleanup

To remove all deployed resources:

```bash
make agentcore-gateway-cleanup
```

**Note:** This does NOT delete the Lambda function or S3 bucket. Delete those manually via AWS Console or CLI if needed.

## Environment Variables

Optional test user credentials (defaults provided):
- `COGNITO_TEST_USERNAME` (default: `testuser`)
- `COGNITO_TEST_PASSWORD` (default: `TestPassword123!`)
- `COGNITO_TEST_EMAIL` (default: `testuser@example.com`)

