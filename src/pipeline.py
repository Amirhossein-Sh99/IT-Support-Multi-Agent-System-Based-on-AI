"""
Shared pipeline logic.

Both main.py (CLI) and streamlit_app.py (web UI) call process_ticket() so
there's exactly one place that actually runs the agent pipeline.
"""

import os
import re

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.orchestrator import it_support_pipeline

APP_NAME = "it_support_agents"
USER_ID = "demo_user"


def extract_field(text: str, field_name: str) -> str:
    """Pulls a 'Field: value' line out of an agent's structured text output.

    Both Triage ("Category: network") and Diagnostics ("Root Cause: ...")
    agents are instructed to end their response in this format, so this one
    helper covers both - used to populate real (not placeholder) values when
    saving to long-term memory and for the dashboard view.
    """
    match = re.search(rf"{field_name}:\s*(.+)", text)
    return match.group(1).strip() if match else "unknown"


async def process_ticket(ticket_text: str) -> str:
    """Runs a ticket through the full Triage -> Diagnostics -> Documentation
    pipeline and returns the final documentation report as a string.

    Raises:
        RuntimeError: if GOOGLE_API_KEY is not set.
    """
    final_report = ""
    async for step in process_ticket_streaming(ticket_text):
        if step["agent"] == "documentation_agent":
            final_report = step["text"]
    return final_report


async def process_ticket_streaming(ticket_text: str):
    """Same pipeline as process_ticket, but yields a dict after each agent
    finishes: {"agent": <name>, "text": <that agent's output>}. Lets a UI
    show live progress across Triage -> Diagnostics -> Documentation instead
    of waiting silently for the whole pipeline to finish.

    Raises:
        RuntimeError: if GOOGLE_API_KEY is not set.
    """
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add it to your .env file (local) "
            "or Streamlit secrets (deployed)."
        )

    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)

    runner = Runner(
        agent=it_support_pipeline,
        app_name=APP_NAME,
        session_service=session_service,
    )

    user_message = types.Content(role="user", parts=[types.Part(text=ticket_text)])

    async for event in runner.run_async(
        user_id=USER_ID, session_id=session.id, new_message=user_message
    ):
        if event.content and event.content.parts and event.content.parts[0].text:
            author = getattr(event, "author", None)
            if author in ("triage_agent", "diagnostics_agent", "documentation_agent"):
                yield {"agent": author, "text": event.content.parts[0].text}
