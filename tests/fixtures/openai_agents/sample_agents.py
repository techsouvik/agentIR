from agents import Agent

triage_agent = Agent(
    name="Triage Assistant",
    model="gpt-4o",
    instructions="Triage incoming support queries and route them to specialists.",
)
