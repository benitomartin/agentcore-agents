# AgentCore Agents

<div align="center">

<!-- Project Status -->

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

<!-- Providers -->

[![AWS](https://img.shields.io/badge/AWS-232F3E?logo=amazon-aws)](https://aws.amazon.com/)
[![Bedrock AgentCore](https://img.shields.io/badge/Bedrock%20AgentCore-FF9900?logo=amazon-aws)](https://aws.amazon.com/bedrock/agentcore/)

</div>

## Table of Contents

- [AgentCore Agents](#agentcore-agents)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Project Structure](#project-structure)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Configuration](#configuration)
    - [Deployment](#deployment)
    - [Local Testing](#local-testing)
    - [Deployed Agent Testing](#deployed-agent-testing)
    - [Quality Checks](#quality-checks)
  - [License](#license)

## Overview

AgentCore Agents is a Python project that provides a unified agent architecture for AWS Bedrock AgentCore.  
It supports both local and Gateway-based tool execution with persistent memory, enabling conversational AI agents that can interact with AWS services through Lambda functions exposed via the AgentCore Gateway.

**Key Features:**
- Unified agent wrapper supporting Gateway tools via MCP (Model Context Protocol)
- Persistent memory using AgentCore Memory service
- User authentication via Amazon Cognito
- Gateway integration for Lambda-based tools
- Runtime deployment for production use

## Project Structure

```text
agentcore-agents/
├── src/
│   └── agentcore_agents/
│       ├── __init__.py
│       ├── agent.py                                    # Main StrandsAgentWrapper class
│       ├── config.py                                   # Configuration settings
│       ├── auth/                                       # Authentication modules
│       │   ├── cognito.py                              # Cognito user authentication
│       │   ├── secrets_manager.py                      # AWS Secrets Manager integration
│       │   └── user_identity.py                        # JWT token parsing
│       ├── gateway/                                    # Gateway setup and management
│       │   └── setup.py                                # Gateway creation and configuration
│       ├── lambda/                                     # Lambda function handlers
│       │   ├── handler.py                              # Tool implementations (calculator, time, S3)
│       │   └── tool_schema.json                        # Tool schema definitions
│       ├── memory/                                     # Memory management
│       │   ├── hooks.py                                # Memory hooks for agent integration
│       │   ├── manager.py                              # Memory manager wrapper
│       │   └── session.py                              # Session management
│       └── prompts/                                    # System prompts
│           └── system.py                               # Agent system prompt
├── scripts/                                            # Deployment and setup scripts
│   ├── deploy_lambda.py                                # Deploy Lambda function
│   ├── setup_gateway.py                                # Setup Gateway and Cognito
│   ├── setup_runtime_permissions.py                    # Add IAM permissions for runtime
│   ├── setup_s3.py                                     # Create S3 bucket
│   └── setup_user_auth.py                              # Create test user in Cognito
├── tests/                                              # Test files
│   ├── test_agent_with_user_identity.py                # Test with user authentication
│   └── test_gateway_auth_rejection.py                  # Test authentication rejection
├── .bedrock_agentcore.yaml                             # AgentCore runtime configuration
├── DEPLOYMENT_GUIDE.md                                 # Detailed deployment instructions
├── Makefile                                            # Build and deployment commands
├── pyproject.toml                                      # Project dependencies and config
├── runtime_handler.py                                  # AgentCore Runtime entrypoint
└── README.md                                           # This file
```

## Prerequisites

- Python 3.13+
- AWS CLI configured with appropriate credentials
- AWS account with access to:
  - Amazon Bedrock AgentCore
  - AWS Lambda
  - Amazon Cognito
  - Amazon S3
  - AWS Secrets Manager
  - AWS IAM
- `uv` package manager (from Astral)

## Installation

1. Clone the repository:

   ```bash
   git clone git@github.com:benitomartin/agentcore-agents.git
   cd agentcore-agents
   ```

2. Create a virtual environment:

   ```bash
   uv venv
   ```

3. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

4. Install the required packages:

   ```bash
   uv sync --all-groups --all-extra
   ```

5. Create a `.env` file in the root directory with your AWS configuration:

   ```bash
   # Example .env file
   AWS_REGION=eu-central-1
   GATEWAY__NAME=AgentGateway
   GATEWAY__GATEWAY_URL=https://...
   MEMORY__NAME=AgentMemory
   MEMORY__SESSION_ID=default-session
   ```

## Usage

### Configuration

Configure AWS settings, Gateway URLs, and memory settings by editing:

- `src/agentcore_agents/config.py` - Main configuration using Pydantic settings
- `.env` file - Environment variables for runtime configuration

### Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

Quick deployment steps:

1. **Setup S3 bucket:**
   ```bash
   make agentcore-s3-setup
   ```

2. **Deploy Lambda function:**
   ```bash
   make agentcore-lambda-deploy
   ```

3. **Setup Gateway and Cognito:**
   ```bash
   make agentcore-gateway
   ```

4. **Create test user:**
   ```bash
   uv run scripts/setup_user_auth.py
   ```

5. **Configure and deploy agent:**
   ```bash
   uv run agentcore configure
   uv run agentcore deploy
   ```

6. **Add runtime permissions:**
   ```bash
   uv run scripts/setup_runtime_permissions.py
   ```

### Local Testing

Test the agent locally with Gateway tools:

```bash
uv run tests/test_agent_with_user_identity.py
```

This test:
- Authenticates with Cognito
- Connects to Gateway via MCP
- Executes tools (calculator, get_current_time, read_s3_document)
- Uses persistent memory across conversations

### Deployed Agent Testing

Test the deployed agent:

```bash
# Get user token
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

# Invoke deployed agent
uv run agentcore invoke '{"prompt": "What is 2 + 2?"}' --bearer-token "$TOKEN"
```

### Quality Checks

Run all quality checks (lint, format, type check, clean):

```bash
make all-check
```

Fix code formatting and linting:

```bash
make all-fix
```

Individual Commands:

- Display all available commands:
  ```bash
  make help
  ```

- Check code formatting and linting:
  ```bash
  make all-check
  ```

- Fix code formatting and linting:
  ```bash
  make all-fix
  ```

- Run type checking:
  ```bash
  make mypy
  ```

- Clean cache and build files:
  ```bash
  make clean
  ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.