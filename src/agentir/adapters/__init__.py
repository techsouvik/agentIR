"""Framework adapters for AgentIR."""

from agentir.adapters.agno.adapter import AgnoAdapter
from agentir.adapters.base import FrameworkAdapter
from agentir.adapters.crewai.adapter import CrewAIAdapter
from agentir.adapters.langgraph.adapter import LangGraphAdapter
from agentir.adapters.lyzr.adapter import LyzrAdapter
from agentir.adapters.mcp.adapter import MCPAdapter
from agentir.adapters.openai_agents.adapter import OpenAIAgentsAdapter
from agentir.adapters.registry import (
    get_adapter,
    list_registered_adapters,
    register_adapter,
)

# Register all built-in framework adapters
register_adapter("langgraph", LangGraphAdapter)
register_adapter("agno", AgnoAdapter)
register_adapter("openai_agents", OpenAIAgentsAdapter)
register_adapter("openai", OpenAIAgentsAdapter)
register_adapter("lyzr", LyzrAdapter)
register_adapter("mcp", MCPAdapter)
register_adapter("crewai", CrewAIAdapter)

__all__ = [
    "AgnoAdapter",
    "CrewAIAdapter",
    "FrameworkAdapter",
    "LangGraphAdapter",
    "LyzrAdapter",
    "MCPAdapter",
    "OpenAIAgentsAdapter",
    "get_adapter",
    "list_registered_adapters",
    "register_adapter",
]
