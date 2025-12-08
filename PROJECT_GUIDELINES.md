# Agentcore Project


## Links

CLI Commands

https://docs.aws.amazon.com/cli/latest/reference/bedrock-agentcore-control/

Agentcore
https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-get-started-toolkit.html

Agentcore Examples
https://github.com/awslabs/amazon-bedrock-agentcore-samples

Strands Agents
https://github.com/strands-agents/sdk-python

## Implementations

- Runtime
- Gateway

https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-quick-start.html

https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-supported-targets.html

- Tools
- Identity

https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/security-iam.html

https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/01-tutorials/03-AgentCore-identity

- Memory

https://github.com/awslabs/amazon-bedrock-agentcore-samples/blob/main/01-tutorials/04-AgentCore-memory/01-short-term-memory/01-single-agent/with-strands-agent/personal-agent-memory-manager.ipynb

https://docs.aws.amazon.com/cli/latest/reference/bedrock-agentcore-control/create-memory.html

Use this snippet to your agent code to write events to memory and retrieve events from memory records.


```python
if event_timestamp is None:
                event_timestamp = datetime.utcnow()

            params = {
                "memoryId": memory_id,
                "actorId": actor_id,
                "sessionId": session_id,
                "eventTimestamp": event_timestamp,
                "payload": payload,
                "clientToken": str(uuid.uuid4()),
            }
            response = memory_client.create_event(**params)

            event = response["event"]
            logger.info("Created event: %s", event["eventId"])
```


Can you search in Amazon the book LLM Engineer's Handbook and tell me the price?