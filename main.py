"""
CLI entry point.

Runs a sample IT support ticket through the full Triage -> Diagnostics ->
Documentation pipeline and prints the final report.

Usage:
    python main.py
    python main.py "My VPN keeps disconnecting every few minutes"
"""

import sys
import asyncio

from dotenv import load_dotenv
load_dotenv()

from src.pipeline import process_ticket_streaming, extract_field
from src.memory import save_ticket


async def run_ticket(ticket_text: str) -> None:
    print(f"\n=== Incoming Ticket ===\n{ticket_text}\n")

    results = {}
    try:
        async for update in process_ticket_streaming(ticket_text):
            results[update["agent"]] = update["text"]
            print(f"--- {update['agent']} ---")
            print(update["text"])
            print()
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Pull real category/urgency/root-cause/fix out of the agents' structured
    # output, instead of saving placeholder values, so memory (and the
    # dashboard view) reflect what actually happened.
    triage_text = results.get("triage_agent", "")
    diagnostics_text = results.get("diagnostics_agent", "")

    save_ticket(
        ticket_text=ticket_text,
        category=extract_field(triage_text, "Category"),
        urgency=extract_field(triage_text, "Urgency"),
        root_cause=extract_field(diagnostics_text, "Root Cause"),
        fix=extract_field(diagnostics_text, "Proposed Fix"),
    )


if __name__ == "__main__":
    default_ticket = (
        "I can't connect to the office VPN since this morning. "
        "It was working fine yesterday."
    )
    ticket = sys.argv[1] if len(sys.argv) > 1 else default_ticket
    asyncio.run(run_ticket(ticket))
