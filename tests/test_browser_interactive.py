import nest_asyncio
from loguru import logger
from strands import Agent
from strands.models import BedrockModel

from agentcore_agents.config import settings
from agentcore_agents.tools.registry import TOOLS

nest_asyncio.apply()


def main() -> None:
    logger.info("Interactive Browser Agent Session")
    logger.info("=" * 60)
    logger.info("This is an interactive session where you can guide the agent")
    logger.info("Type 'quit' or 'exit' to end the session")
    logger.info("=" * 60)

    logger.info("\nCreating agent with browser tool...")
    agent = Agent(
        model=BedrockModel(
            model_id=settings.model.model_id,
            region_name=settings.aws.region,
            max_tokens=settings.model.max_tokens,
        ),
        tools=TOOLS,
    )

    logger.info(f"✓ Agent created with {len(TOOLS)} tools")
    logger.info("Tools: calculator, get_current_time, browser")
    logger.info("\n" + "=" * 60)

    conversation_count = 0

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                logger.info("\nEnding session. Goodbye!")
                break

            conversation_count += 1
            logger.info(f"\n[Conversation {conversation_count}]")
            logger.info(f"Processing: {user_input}")

            try:
                response = agent(user_input)
                agent_text = response.message["content"][0]["text"]

                logger.info("\nAgent:")
                print(agent_text)

                if hasattr(response, "tool_calls") and response.tool_calls:
                    logger.info(f"\n[Agent used {len(response.tool_calls)} tool(s)]")

            except RuntimeError as e:
                if "Timeout should be used inside a task" in str(e):
                    logger.warning("Asyncio cleanup warning (tool still worked)")
                else:
                    logger.error(f"Error: {e}")
            except Exception as e:
                logger.error(f"Error: {e}")
                logger.info("Try rephrasing your request or check the error above")

        except KeyboardInterrupt:
            logger.info("\n\nSession interrupted. Goodbye!")
            break
        except EOFError:
            logger.info("\n\nEnding session. Goodbye!")
            break

    logger.info(f"\nSession ended after {conversation_count} conversation(s)")


if __name__ == "__main__":
    main()
