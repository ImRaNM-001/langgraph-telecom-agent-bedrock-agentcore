import uuid

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
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
    # Pre-model hook: saves messages and retrieves long-term memories
    def pre_model_hook(self, state: AgentState, config: RunnableConfig, *, store: BaseStore):
        """
        Hook that runs before LLM invocation to:
        1. Save the latest human message to long-term memory
        2. Retrieve relevant user preferences and memories
        3. Append memories to the context
        """
        actor_id = config["configurable"]["actor_id"]
        thread_id = config["configurable"]["thread_id"]

        # Namespace for this specific session
        namespace = (actor_id, thread_id)
        messages = state.get("messages", [])

        # Save the last human message to long-term memory
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                store.put(namespace, str(uuid.uuid4()), {"message": msg})

                # OPTIONAL: Retrieve user preferences from long-term memory
                # Search across all sessions for this actor
                user_preferences_namespace = ("preferences", actor_id)
                try:
                    preferences = store.search(
                        user_preferences_namespace,
                        query=msg.content,
                        limit=5
                    )

                    # If we found relevant memories, add them to the context
                    if preferences:
                        memory_context = "\n".join([
                            f"Memory: {item.value.get('message', '')}"
                            for item in preferences
                        ])
                        # You can append this to the messages or use it another way
                        print(f"Retrieved memories: {memory_context}")
                except Exception as e:
                    print(f"Memory retrieval error: {e}")
                break

        return {"messages": messages}

    # OPTIONAL: Post-model hook to save AI responses
    def post_model_hook(state, config: RunnableConfig, *, store: BaseStore):
        """
        Hook that runs after LLM invocation to save AI messages to long-term memory
        """
        actor_id = config["configurable"]["actor_id"]
        thread_id = config["configurable"]["thread_id"]
        namespace = (actor_id, thread_id)

        messages = state.get("messages", [])

        # Save the last AI message
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                store.put(namespace, str(uuid.uuid4()), {"message": msg})
                break

        return state
