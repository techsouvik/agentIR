from agno.agent import Agent
from agno.models.openai import OpenAIChat


def search_knowledge_base(query: str) -> str:
    """Search the internal knowledge base for relevant articles."""
    return f"Results for {query}"

support_agent = Agent(
    name="Support Specialist",
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a customer support agent. Help users resolve issues politely.",
    tools=[search_knowledge_base],
    markdown=True,
)
