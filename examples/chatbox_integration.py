"""Example: How to invoke deployed AgentCore agent from a chatbox/frontend.

This shows the HTTP API pattern for calling your deployed agent.
"""

import json
from typing import Any

import requests


def invoke_agent_from_chatbox(
    agent_id: str,
    region: str,
    user_token: str,
    prompt: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Invoke deployed AgentCore agent via HTTP API.
    
    Args:
        agent_id: Your agent ID (e.g., 'runtime_handler-0hrJUv8Rj2')
        region: AWS region (e.g., 'eu-central-1')
        user_token: Cognito access token (JWT) from user authentication
        prompt: User's message/prompt
        session_id: Optional session ID for conversation continuity
    
    Returns:
        Agent response as dict
    """
    # AgentCore Runtime endpoint format
    endpoint = f"https://runtime.bedrock-agentcore.{region}.amazonaws.com/runtime/{agent_id}/invoke"
    
    # Request payload
    payload = {
        "prompt": prompt,
    }
    if session_id:
        payload["session_id"] = session_id
    
    # Headers with authentication
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_token}",
    }
    
    # Make HTTP POST request
    response = requests.post(
        endpoint,
        json=payload,
        headers=headers,
        timeout=60,  # Agent responses can take time
    )
    
    response.raise_for_status()
    return response.json()


# Example usage in a chatbox/frontend:
def example_chatbox_flow():
    """Example showing how a chatbox would use this."""
    
    # 1. User authenticates with Cognito (in your frontend)
    # This happens in your frontend/auth layer
    user_token = "eyJraWQiOiJ..."  # JWT from Cognito
    
    # 2. Get agent ID from your config
    agent_id = "runtime_handler-0hrJUv8Rj2"
    region = "eu-central-1"
    
    # 3. User sends message in chatbox
    user_message = "What is 2 + 2?"
    
    # 4. Call agent
    try:
        response = invoke_agent_from_chatbox(
            agent_id=agent_id,
            region=region,
            user_token=user_token,
            prompt=user_message,
            session_id=None,  # Or maintain session across messages
        )
        
        # 5. Extract agent response
        agent_response = response.get("response", {}).get("content", [{}])[0].get("text", "")
        print(f"Agent: {agent_response}")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Authentication failed - token expired or invalid")
        elif e.response.status_code == 403:
            print("Forbidden - check IAM permissions")
        else:
            print(f"Error: {e}")


# Frontend JavaScript example (for reference):
FRONTEND_JS_EXAMPLE = """
// JavaScript/TypeScript example for React/Next.js chatbox

async function sendMessageToAgent(userMessage, userToken, sessionId = null) {
  const agentId = 'runtime_handler-0hrJUv8Rj2';
  const region = 'eu-central-1';
  const endpoint = `https://runtime.bedrock-agentcore.${region}.amazonaws.com/runtime/${agentId}/invoke`;
  
  const payload = {
    prompt: userMessage,
    ...(sessionId && { session_id: sessionId })
  };
  
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${userToken}`
    },
    body: JSON.stringify(payload)
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

// Usage in React component:
function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [userToken, setUserToken] = useState(null); // From Cognito auth
  
  const handleSend = async (userMessage) => {
    try {
      const response = await sendMessageToAgent(userMessage, userToken);
      const agentResponse = response.response?.content?.[0]?.text || 'No response';
      
      setMessages(prev => [
        ...prev,
        { role: 'user', content: userMessage },
        { role: 'agent', content: agentResponse }
      ]);
    } catch (error) {
      console.error('Error calling agent:', error);
    }
  };
  
  return (
    // Your chatbox UI here
  );
}
"""


if __name__ == "__main__":
    print("This is an example file showing how to invoke the agent from a chatbox.")
    print("\nKey points:")
    print("1. Endpoint: https://runtime.bedrock-agentcore.{region}.amazonaws.com/runtime/{agent_id}/invoke")
    print("2. Method: POST")
    print("3. Headers: Authorization: Bearer {cognito_token}")
    print("4. Body: { 'prompt': 'user message', 'session_id': 'optional' }")
    print("\nSee FRONTEND_JS_EXAMPLE for JavaScript/React example.")

