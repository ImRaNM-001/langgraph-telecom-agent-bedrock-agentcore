from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

from src.config import params, get_secret
from src.memory import get_checkpointer, get_store, MemoryMiddleware
from src.tools import tools


def build_agent():
    """Create the Lauki Phones FAQ agent with AgentCore short-term and long-term memory."""
    # Initialize the LLM
    llm = init_chat_model(
        model=params.agent.model,
        model_provider=params.agent.model_provider,
        temperature=params.agent.temperature,
        api_key=get_secret("GROQ_API_KEY"),
    )

    # Create the agent with memory configurations
    agent = create_agent(
        model=llm,
        tools=tools,
        checkpointer=get_checkpointer(),
        store=get_store(),
        middleware=[MemoryMiddleware()],
        system_prompt=params.agent.system_prompt,
    )
    return agent
