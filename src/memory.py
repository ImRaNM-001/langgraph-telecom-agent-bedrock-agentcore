import uuid

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_config
from langgraph.runtime import Runtime
from langchain.agents.middleware import AgentMiddleware, AgentState
from langgraph.store.base import BaseStore
from langgraph_checkpoint_aws import AgentCoreMemorySaver, AgentCoreMemoryStore

from src.config import get_secret
from src.logging import logger

_checkpointer = None
_store = None


def get_checkpointer() -> AgentCoreMemorySaver:
    """Short-term memory: AgentCore Memory-backed LangGraph checkpointer."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = AgentCoreMemorySaver(memory_id=get_secret("MEMORY_ID"))
    return _checkpointer


def get_store() -> AgentCoreMemoryStore:
    """Long-term memory: AgentCore Memory-backed LangGraph store."""
    global _store
    if _store is None:
        _store = AgentCoreMemoryStore(memory_id=get_secret("MEMORY_ID"))
    return _store


class MemoryMiddleware(AgentMiddleware):
    """Persist conversation events and expose semantic memories to the model."""

    @staticmethod
    def _identity() -> tuple[str, str]:
        config: RunnableConfig = get_config()
        configurable = config["configurable"]
        return configurable["actor_id"], configurable["thread_id"]

    @staticmethod
    def _store(runtime: Runtime) -> BaseStore:
        if runtime.store is None:
            raise RuntimeError("AgentCore Memory store is not configured")
        return runtime.store

    def before_agent(self, state: AgentState, runtime: Runtime) -> dict | None:
        """Save the user turn and add relevant cross-session facts to context."""
        actor_id, thread_id = self._identity()
        store = self._store(runtime)
        messages = state.get("messages", [])

        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                store.put((actor_id, thread_id), str(uuid.uuid4()), {"message": message})
                break

        preferences = store.search(
            ("preferences", actor_id),
            query=messages[-1].content if messages else "user preferences",
            limit=5,
        )
        if not preferences:
            return None

        logger.info("RAW MEMORY ITEMS: %r", preferences)
        # memories = "\n".join(item.value["content"] for item in preferences)
        memories = "\n".join(
            item.value["content"]["text"] if isinstance(item.value.get("content"), dict)
            else str(item.value.get("content", ""))
            for item in preferences
        )
        logger.info("Retrieved %d semantic memory record(s) for actor %s", len(preferences), actor_id)
        return {
            "messages": [
                SystemMessage(
                    content=(
                        "Relevant user memories from prior conversations:\n"
                        f"{memories}\n"
                        "Use these only when they help answer the user."
                    )
                )
            ]
        }

    def after_agent(self, state: AgentState, runtime: Runtime) -> None:
        """Save the final assistant response as a conversational event."""
        actor_id, thread_id = self._identity()
        store = self._store(runtime)

        for message in reversed(state.get("messages", [])):
            if isinstance(message, AIMessage):
                store.put((actor_id, thread_id), str(uuid.uuid4()), {"message": message})
                return None
        return None
