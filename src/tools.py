from langchain_core.tools import tool

from src.config import params
from src.vector_store import get_faq_store


@tool
def search_faq(query: str) -> str:
    """Search the FAQ knowledge base for relevant information.
    Use this tool when the user asks questions about products, services, or policies.

    Args:
        query: The search query to find relevant FAQ entries

    Returns:
        Relevant FAQ entries that might answer the question
    """
    results = get_faq_store().similarity_search(query, k=params.knowledge_base.search_k)

    if not results:
        return "No relevant FAQ entries found."

    context = "\n\n---\n\n".join([
        f"FAQ Entry {i+1}:\n{doc.page_content}"
        for i, doc in enumerate(results)
    ])

    return f"Found {len(results)} relevant FAQ entries:\n\n{context}"


@tool
def search_detailed_faq(query: str, num_results: int = None) -> str:
    """Search the FAQ knowledge base with more results for complex queries.
    Use this when the initial search doesn't provide enough information.

    Args:
        query: The search query
        num_results: Number of results to retrieve (default: configured detailed_search_k)

    Returns:
        More comprehensive FAQ entries
    """
    if num_results is None:
        num_results = params.knowledge_base.detailed_search_k
    results = get_faq_store().similarity_search(query, k=num_results)

    if not results:
        return "No relevant FAQ entries found."

    context = "\n\n---\n\n".join([
        f"FAQ Entry {i+1}:\n{doc.page_content}"
        for i, doc in enumerate(results)
    ])

    return f"Found {len(results)} detailed FAQ entries:\n\n{context}"


@tool
def reformulate_query(original_query: str, focus_aspect: str) -> str:
    """Reformulate the query to focus on a specific aspect.
    Use this when you need to search for a different angle of the question.

    Args:
        original_query: The original user question
        focus_aspect: The specific aspect to focus on (e.g., "pricing", "activation", "troubleshooting")

    Returns:
        A reformulated query focused on the specified aspect
    """
    reformulated = f"{focus_aspect} related to {original_query}"
    results = get_faq_store().similarity_search(reformulated, k=params.knowledge_base.search_k)

    if not results:
        return f"No results found for aspect: {focus_aspect}"

    context = "\n\n---\n\n".join([
        f"Entry {i+1}:\n{doc.page_content}"
        for i, doc in enumerate(results)
    ])

    return f"Results for '{focus_aspect}' aspect:\n\n{context}"


tools = [search_faq, search_detailed_faq, reformulate_query]
