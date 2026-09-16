from typing import Annotated, TypedDict

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: str

def call_model(_state: State):
    return {"messages": ["AI response"]}

def call_tool(_state: State):
    return {"messages": ["Tool output"]}

def route_decision(_state: State):
    return "call_tool"

builder = StateGraph(State)
builder.add_node("agent", call_model)
builder.add_node("tools", call_tool)
builder.set_entry_point("agent")
builder.add_conditional_edges("agent", route_decision, {"call_tool": "tools", "finish": "END"})
builder.add_edge("tools", "agent")
graph = builder.compile()
