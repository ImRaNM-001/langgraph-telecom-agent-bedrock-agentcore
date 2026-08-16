from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.agent import build_agent
from src.config import params

# Create the AgentCore app instance
app = BedrockAgentCoreApp()

agent = build_agent()


# AgentCore Entrypoint
@app.entrypoint
def agent_invocation(payload, context):
    """Handler for agent invocation in AgentCore runtime with memory support"""
    print("Received payload:", payload)
    print("Context:", context)

    # Extract query from payload
    query = payload.get("prompt", "No prompt found in input")

    # Extract or generate actor_id and thread_id
    actor_id = payload.get("actor_id", params.memory.default_actor_id)
    thread_id = payload.get(
        "thread_id",
        payload.get("session_id", f"{params.memory.default_session_prefix}-default"),
    )

    # Configure memory context
    config = {
        "configurable": {
            "thread_id": thread_id,  # Maps to AgentCore session_id
            "actor_id": actor_id     # Maps to AgentCore actor_id
        }
    }

    # Invoke the agent with memory
    result = agent.invoke(
        {"messages": [("human", query)]},
        config=config
    )

    print("Result:", result)

    # Extract the final answer from the result
    messages = result.get("messages", [])
    answer = messages[-1].content if messages else "No response generated"

    # Return the answer
    return {
        "result": answer,
        "actor_id": actor_id,
        "thread_id": thread_id
    }


if __name__ == "__main__":
    app.run()
