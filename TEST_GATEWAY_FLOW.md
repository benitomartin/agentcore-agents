# Gateway Authentication and Testing Flow

This document explains the authentication flows and test scripts for the AgentCore Gateway, including user authentication, token management, and gateway interaction.

## Overview

The Gateway uses OAuth 2.0 with Amazon Cognito for authentication. There are two authentication flows:

1. **Client Credentials Flow** (machine-to-machine) - Used by Gateway setup internally
2. **User Password Flow** (user authentication) - Used by agents to access Gateway with user identity

All test scripts connect to the Gateway using the MCP (Model Context Protocol) over HTTP.

## Test Scripts

### 1. `tests/test_agent_with_user_identity.py`

**Purpose**: Comprehensive test of Gateway with user authentication, agent execution, and memory persistence.

**Authentication Flow**: User Password OAuth Flow

**What it tests**:
- Gateway connection with user authentication
- Tool discovery from Gateway
- Agent execution with Gateway tools
- User identity extraction from JWT
- Memory persistence per user/session
- Multi-turn conversations with context

**Flow**:

1. **Get Gateway Info**: Retrieves Gateway URL and Cognito client info from Gateway
2. **Create/Update User**: 
   - Updates Cognito client to support `USER_PASSWORD_AUTH`
   - Creates test user in Cognito (or uses existing)
3. **Get User Token**:
   - Authenticates user with username/password
   - Receives JWT access token from Cognito
4. **Extract User Identity**:
   - Decodes JWT to get `sub` (user ID) and other claims
   - Uses `sub` as `actor_id` for memory
   - Generates unique `session_id`
5. **Connect to Gateway**:
   - Creates MCP client with user's access token
   - Lists available tools from Gateway
6. **Create Agent**:
   - Creates Strands Agent with Gateway tools
   - Initializes memory with user's `actor_id` and `session_id`
7. **Execute Queries**:
   - Agent processes prompts
   - Calls tools through Gateway
   - Maintains conversation context in memory

**Key Features**:
- Each user has separate memory (`actor_id` from JWT `sub`)
- Each session maintains conversation context
- Memory persists across multiple queries in the same session

### 2. `tests/test_gateway_auth_rejection.py`

**Purpose**: Security test to verify Gateway correctly rejects unauthorized access.

**What it tests**:
- Gateway rejects requests without authentication token
- Gateway rejects requests with invalid/malformed tokens
- Only valid Cognito JWT tokens are accepted

**Flow**:

1. **Get Gateway Info**: Retrieves Gateway URL
2. **Test 1 - No Token**:
   - Attempts to connect without `Authorization` header
   - Verifies Gateway returns 401/Unauthorized error
3. **Test 2 - Invalid Token**:
   - Attempts to connect with invalid JWT token
   - Verifies Gateway rejects the request

**Security Validation**:
- Gateway enforces JWT validation on every request
- No tools accessible without valid authentication
- Protects Lambda functions from unauthorized access

## Authentication Flow Diagram

### User Authentication Flow

```
┌─────────────────────────┐
│ test_agent_with_user    │
│    _identity.py         │
└──────────┬──────────────┘
           │
           │ 1. Get Gateway & Cognito info
           ▼
┌─────────────────────────┐
│ GatewaySetup            │
│ get_client_info_from_   │
│   gateway()              │
└──────────┬──────────────┘
           │
           │ 2. Create/update user in Cognito
           ▼
┌─────────────────────────┐
│ Amazon Cognito          │
│  User Pool              │
└──────────┬──────────────┘
           │
           │ 3. Authenticate user (username/password)
           │    Returns JWT access_token
           ▼
┌─────────────────────────┐
│ Extract User Identity   │
│ (sub → actor_id)         │
└──────────┬──────────────┘
           │
           │ 4. Create MCP Client with user token
           ▼
┌─────────────────────────┐
│ MCP Client              │
│ (with Bearer token)     │
└──────────┬──────────────┘
           │
           │ 5. HTTP requests with
           │    Authorization: Bearer <user_token>
           ▼
┌─────────────────────────┐
│ Agent Gateway           │
│ (validates JWT)         │
└──────────┬──────────────┘
           │
           │ 6. Routes to Lambda targets
           ▼
┌─────────────────────────┐
│ Lambda Function         │
│  (executes tools)       │
└─────────────────────────┘
           │
           │ 7. Results + Memory updates
           ▼
┌─────────────────────────┐
│ Strands Agent           │
│ (with user memory)      │
└─────────────────────────┘
```

## OAuth 2.0 User Password Flow

**What happens when getting a user token**:

1. **HTTP POST Request** to Cognito token endpoint
   - Request body includes:
     - `grant_type`: `password` (USER_PASSWORD_AUTH)
     - `client_id`: OAuth client ID
     - `client_secret`: OAuth client secret (for secret hash)
     - `username`: Cognito username
     - `password`: User password
     - `scope`: `AgentGateway/invoke`

2. **Cognito validates credentials** and returns:
   - `access_token`: JWT containing user identity claims (`sub`, `email`, etc.)
   - `token_type`: `Bearer`
   - `expires_in`: Token lifetime
   - `refresh_token`: For token refresh

3. **JWT contains user identity**:
   - `sub`: Unique user identifier (used as `actor_id` for memory)
   - `email`: User email
   - `iss`: Issuer (Cognito User Pool)
   - `aud`: Audience (client ID)
   - `exp`: Expiration timestamp

## Gateway Tool Invocation Flow

**What happens when agent calls a tool**:

1. Agent decides to use a tool (e.g., `read_s3_document`)
2. **MCP Client** sends `tools/call` request to Gateway:
   - HTTP POST to Gateway MCP URL
   - `Authorization: Bearer <user_token>` header
   - Tool name and parameters in request body
3. **Gateway validates token**:
   - Verifies JWT signature
   - Checks expiration
   - Validates issuer (Cognito User Pool)
   - Verifies scope (`AgentGateway/invoke`)
4. **Gateway routes to Lambda**:
   - Identifies Lambda target for the tool
   - Invokes Lambda function with tool name and parameters
   - Passes user identity context (from JWT) to Lambda
5. **Lambda executes tool**:
   - Receives tool invocation request
   - Executes Python function (e.g., `read_s3_document()`)
   - Returns result
6. **Gateway returns result** to MCP Client
7. **Agent receives result** and continues processing

## Security Notes

1. **Token Validation**: Gateway validates JWT on each request (signature, expiration, scope, issuer)
2. **Token Expiration**: Tokens expire; client must refresh using refresh token
3. **Scope**: `AgentGateway/invoke` limits what the token can do
4. **User Identity**: JWT `sub` claim uniquely identifies users for memory isolation
5. **No Token = No Access**: Gateway rejects all requests without valid authentication

## Key Components

- **Gateway URL**: MCP endpoint URL (retrieved from Gateway)
- **Cognito User Pool**: Manages user authentication
- **Cognito Client**: OAuth client configured for Gateway
- **User Access Token**: JWT from Cognito (contains user identity)
- **MCP Client**: Handles MCP protocol over HTTP with authentication
- **Actor ID**: User identifier extracted from JWT `sub` claim
- **Session ID**: Unique identifier for conversation sessions

## Memory and User Identity

- **Actor ID**: Extracted from JWT `sub` claim, uniquely identifies each user
- **Session ID**: Unique identifier for each conversation session
- **Memory Isolation**: Each user (`actor_id`) has separate memory
- **Session Context**: Each session maintains conversation history
- **Memory Persistence**: Events stored in AgentCore Memory service, inked to `actor_id` and `session_id`

## Summary

The Gateway uses OAuth 2.0 User Password flow for user authentication, with JWT tokens containing user identity claims. The Gateway validates tokens on every request, ensuring only authenticated users can access Lambda tools. User identity from the JWT (`sub` claim) is used to isolate memory and maintain conversation context per user and session.
