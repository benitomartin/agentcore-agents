# Test Gateway Flow Explanation

This document explains the step-by-step flow that occurs when running `scripts/test_gateway.py`, including authentication, token management, and gateway interaction.

## Overview

The test script connects to an AWS AgentCore Gateway using the MCP (Model Context Protocol) over HTTP, authenticates via OAuth 2.0 Client Credentials flow with Amazon Cognito, and executes an agent with tools discovered from the Gateway.

## Phase 1: Configuration Loading

### Step 1: Load Gateway Configuration

The script reads `gateway_config.json` (created by `setup_gateway.py`) which contains:

- `gateway_url`: MCP endpoint URL
- `client_info`: Cognito OAuth credentials (client_id, client_secret, token_endpoint, etc.)
- `region`: AWS region
- `gateway_id`: Gateway identifier

## Phase 2: OAuth Authentication

### Step 2: Initialize Gateway Setup

Creates a `GatewaySetup` instance with the region from config.

### Step 3: OAuth Token Request (Client Credentials Flow)

**What happens:**

1. **HTTP POST Request** to Cognito token endpoint (`token_endpoint` from `client_info`)
   - Request body includes:
     - `grant_type`: `client_credentials`
     - `client_id`: OAuth client ID
     - `client_secret`: OAuth client secret
     - `scope`: `AgentGateway/invoke`

2. **Cognito validates credentials** and returns:
   - `access_token`: JWT (Bearer token)
   - `token_type`: `Bearer`
   - `expires_in`: Token lifetime

3. **Script receives** the access token (JWT)

## Phase 3: MCP Connection Setup

### Step 4: Create MCP Transport

Creates an HTTP transport for MCP protocol with:
- Gateway MCP URL
- `Authorization: Bearer <access_token>` header

### Step 5: Initialize MCP Client

Creates MCP client with authenticated transport. The lambda function defers transport creation until needed.

## Phase 4: Gateway Interaction

### Step 6: Connect and List Tools

**What happens:**

1. **Context manager opens** MCP connection
2. **First request validates** the access token:
   - Gateway validates JWT signature
   - Checks expiration
   - Verifies scope (`AgentGateway/invoke`)
   - Validates issuer (Cognito User Pool)
3. **`list_tools_sync()`** sends MCP `tools/list` request:
   - HTTP POST to gateway URL
   - Authorization header with Bearer token
   - Gateway routes to Lambda target(s)
   - Lambda returns available tools
   - Gateway aggregates and returns tool list

## Phase 5: Agent Execution

### Step 7: Create Agent with Gateway Tools

Creates Strands Agent with:
- Bedrock model configuration
- Tools discovered from Gateway

### Step 8: Execute Agent Query

**What happens:**

1. Agent processes prompt
2. **If tool is needed:**
   - Agent calls tool via MCP client
   - MCP client sends authenticated request to Gateway
   - Gateway validates token again
   - Gateway invokes Lambda target
   - Lambda executes tool and returns result
   - Gateway returns result to agent
3. Agent generates final response using tool results

## Authentication Flow Diagram

```
┌─────────────────┐
│  test_gateway   │
│      .py        │
└────────┬────────┘
         │
         │ 1. Load config (client_info)
         ▼
┌─────────────────┐
│ GatewaySetup    │
│ get_access_token│
└────────┬────────┘
         │
         │ 2. POST to Cognito Token Endpoint
         │    (client_id, client_secret, scope)
         ▼
┌─────────────────┐
│ Amazon Cognito   │
│  OAuth Server    │
└────────┬────────┘
         │
         │ 3. Returns JWT access_token
         ▼
┌─────────────────┐
│ MCP Client      │
│ (with Bearer    │
│  token header)  │
└────────┬────────┘
         │
         │ 4. HTTP requests with
         │    Authorization: Bearer <token>
         ▼
┌─────────────────┐
│ Agent Gateway   │
│ (validates JWT) │
└────────┬────────┘
         │
         │ 5. Routes to Lambda targets
         ▼
┌─────────────────┐
│ Lambda Function │
│  (executes      │
│   tools)        │
└─────────────────┘
```

## Security Notes

1. **Token Validation**: Gateway validates JWT on each request (signature, expiration, scope, issuer)
2. **Token Expiration**: Tokens expire; client must refresh
3. **Scope**: `AgentGateway/invoke` limits what the token can do
4. **Client Credentials**: Uses OAuth 2.0 Client Credentials flow (machine-to-machine)

## Key Components

- **`client_info`**: Contains Cognito OAuth credentials (from setup)
- **`access_token`**: JWT from Cognito (validated by Gateway)
- **`gateway_url`**: MCP endpoint URL
- **`MCPClient`**: Handles MCP protocol over HTTP with authentication

## Summary

The flow uses OAuth 2.0 Client Credentials for service-to-service authentication, with the Gateway validating tokens on each request. This ensures secure access to Lambda-based tools through the AgentCore Gateway.
