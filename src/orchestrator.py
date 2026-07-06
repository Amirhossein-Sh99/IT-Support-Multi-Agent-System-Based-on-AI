"""
Orchestrator

Wires Triage -> Diagnostics -> Documentation into a single sequential
pipeline using Google ADK's SequentialAgent workflow pattern. Each sub-agent
writes its output to shared session state, which the next agent reads.
"""

from google.adk.agents import SequentialAgent

from src.agents.triage_agent import triage_agent
from src.agents.diagnostics_agent import diagnostics_agent
from src.agents.documentation_agent import documentation_agent

# output_key tells ADK to store each agent's final response text under that
# key in session.state, making it available to later agents in the sequence.
triage_agent.output_key = "triage_result"
diagnostics_agent.output_key = "diagnostics_result"
documentation_agent.output_key = "documentation_result"

it_support_pipeline = SequentialAgent(
    name="it_support_pipeline",
    description=(
        "End-to-end IT support pipeline: classifies a ticket, diagnoses the "
        "root cause, and produces a bilingual resolution report."
    ),
    sub_agents=[triage_agent, diagnostics_agent, documentation_agent],
)
