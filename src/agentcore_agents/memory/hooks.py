from typing import Any

from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole
from bedrock_agentcore.memory.session import MemorySession
from loguru import logger
from strands.hooks import AgentInitializedEvent, HookProvider, HookRegistry, MessageAddedEvent


class MemoryHookProvider(HookProvider):
    def __init__(self, memory_session: MemorySession, actor_id: str, session_id: str) -> None:
        self.memory_session = memory_session
        self.actor_id = actor_id
        self.session_id = session_id

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        logger.info("Memory hooks registered")

    def on_agent_initialized(self, event: AgentInitializedEvent) -> None:
        self._load_conversation_history(event)

    def on_message_added(self, event: MessageAddedEvent) -> None:
        self._save_message(event)

    def _load_conversation_history(self, event: AgentInitializedEvent) -> None:
        logger.info(
            f"Loading conversation history for actor_id={self.actor_id}, "
            "session_id={self.session_id}"
        )
        try:
            recent_turns = self.memory_session.get_last_k_turns(k=10)
            if not recent_turns:
                return

            context_messages = []
            for turn in recent_turns:
                for message in turn:
                    role = message.get("role", "unknown")
                    content = message.get("content", {})
                    text = content.get("text", "") if isinstance(content, dict) else str(content)
                    context_messages.append(f"{role}: {text}")

            context = "\n".join(context_messages)
            logger.info(
                f"[{self.actor_id}:{self.session_id}] "
                "Context being injected into system prompt:\n{context}"
            )

            if event.agent.system_prompt:
                event.agent.system_prompt += f"\n\nRecent conversation:\n{context}"
            else:
                event.agent.system_prompt = f"Recent conversation:\n{context}"

            logger.info(f"Loaded {len(recent_turns)} conversation turns")
        except Exception as e:
            logger.error(f"Failed to load conversation history: {e}")

    def _save_message(self, event: MessageAddedEvent) -> None:
        try:
            messages = event.agent.messages
            if not messages or len(messages) == 0:
                return

            last_message = messages[-1]
            if not last_message["content"][0].get("text"):
                return

            message_text = last_message["content"][0]["text"]
            message_role = (
                MessageRole.USER if last_message["role"] == "user" else MessageRole.ASSISTANT
            )

            result = self.memory_session.add_turns(
                messages=[ConversationalMessage(message_text, message_role)]
            )

            event_id = result.get("eventId", "unknown")
            logger.info(
                f"[{self.actor_id}:{self.session_id}] Stored message with Event ID: {event_id}, "
                "Role: {message_role.value}"
            )
        except Exception as e:
            logger.error(f"[{self.actor_id}:{self.session_id}] Failed to save message: {e}")
