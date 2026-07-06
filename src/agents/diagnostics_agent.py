"""
Diagnostics Agent

Investigates the root cause of a triaged issue. Its diagnostic capabilities
come from two different places, deliberately kept separate:

1. MCP Server (mcp_server/diagnostics_server.py) — gives the agent "reach":
   network_check, traceroute, search_logs, service_status are all fetched
   over the Model Context Protocol rather than imported as plain Python
   functions, so they could just as easily point at a remote server.
2. Local memory tool (src/memory.py) — gives the agent "know-how": recall of
   how similar tickets were solved before.

See skills/it_diagnostics_skill/skill.md for the procedural playbook this
agent follows (which tool to reach for, in what order) — the Agent Skill
pattern from Day 3 of the course.
"""

import os
import sys

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

from src.memory import find_similar_tickets

# Resolve the MCP server script as an absolute path (independent of the
# caller's working directory) and launch it with the exact same Python
# interpreter that's running this process (sys.executable), rather than the
# bare string "python" - both of these previously assumed the app always
# runs from the project root with "python" on PATH, which broke silently
# when deployed to Streamlit Community Cloud (different working directory
# and interpreter path there than on a local machine).
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MCP_SERVER_PATH = os.path.join(_PROJECT_ROOT, "mcp_server", "diagnostics_server.py")

# Connects to our local diagnostics MCP server as a subprocess over stdio.
# In production this could instead point at a remotely hosted MCP server
# over SSE/HTTP - the agent code wouldn't need to change.
diagnostics_mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[_MCP_SERVER_PATH],
        ),
        timeout=30,
    )
)

DIAGNOSTICS_INSTRUCTION = """You are an IT Support Diagnostics Agent.

You receive a triaged issue (category, urgency, entities, restated issue).
Your job is to find the most likely root cause using the tools available to you:
- network_check: test if a host is reachable (via MCP server)
- traceroute: see hop-by-hop latency to a host (via MCP server)
- search_logs: search recent logs for a keyword or error pattern (via MCP server)
- service_status: check if a specific service is running (via MCP server)
- find_similar_tickets: search memory of past resolved tickets for similar issues

You do NOT follow a fixed sequence of tool calls. For every step, run this loop:
  PLAN: given what you know so far, what's the single most useful next check?
  ACT: call that one tool.
  EVALUATE: does the result give a clear enough signal to state a root cause?
    - If yes: stop calling tools and move to your final answer.
    - If no: go back to PLAN and choose a different tool - but never call more
      than 4 tools total. If you still don't have a clear signal after that,
      state your best hypothesis and say so explicitly rather than guessing
      with false confidence.

Always start the loop by calling find_similar_tickets with the restated issue
- a close match from memory is a strong prior that can shorten the rest of
the loop (sometimes to zero further tool calls).

End your response in exactly this format:
Diagnostic Steps: <numbered list, one line per tool call you made, e.g. "1. find_similar_tickets - no close match. 2. service_status(vpn-client) - stopped.">
Root Cause: <short explanation>
Proposed Fix: <concrete action>
"""

diagnostics_agent = Agent(
    name="diagnostics_agent",
    model="gemini-3.1-flash-lite",
    description="Investigates root cause of IT issues using diagnostic tools.",
    instruction=DIAGNOSTICS_INSTRUCTION,
    tools=[
        diagnostics_mcp_toolset,
        find_similar_tickets,
    ],
)
