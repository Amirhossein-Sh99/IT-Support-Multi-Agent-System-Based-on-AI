"""
Lightweight ticket memory.

Stores resolved tickets to a local JSON file so the system can recall
similar past issues and their fixes — a simple but real demonstration of
the "memory" component covered in the course (Day 3: Context & Memory).

In a production system this would be a vector store (e.g. embeddings +
similarity search) rather than keyword overlap, but keyword overlap is
transparent, dependency-free, and easy to demo/explain in a video.
"""

import json
import os
from datetime import datetime, timezone

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "tickets_memory.json")


def _load() -> list:
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(tickets: list) -> None:
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(tickets, f, ensure_ascii=False, indent=2)


def save_ticket(ticket_text: str, category: str, root_cause: str, fix: str, urgency: str = "unknown") -> dict:
    """Saves a resolved ticket to memory for future recall.

    Args:
        ticket_text: The original user-reported issue.
        category: Triage category (network/hardware/software/access).
        root_cause: The diagnosed root cause.
        fix: The applied or proposed fix.
        urgency: Triage urgency (low/medium/high/critical).

    Returns:
        The saved ticket record.
    """
    tickets = _load()
    record = {
        "ticket_text": ticket_text,
        "category": category,
        "urgency": urgency,
        "root_cause": root_cause,
        "fix": fix,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    tickets.append(record)
    _save(tickets)
    return record


def list_all_tickets() -> list:
    """Returns every ticket in long-term memory, most recent first.

    Used by the Ops Dashboard view to show a real queue rather than a
    single one-off chat exchange.
    """
    return list(reversed(_load()))


def find_similar_tickets(ticket_text: str, max_results: int = 3) -> dict:
    """Finds past tickets that share keywords with the current ticket.

    Args:
        ticket_text: The current ticket's description.
        max_results: Max number of similar past tickets to return.

    Returns:
        A dict with key 'matches': list of past ticket records, most relevant first.
    """
    tickets = _load()
    current_words = set(ticket_text.lower().split())

    scored = []
    for t in tickets:
        past_words = set(t["ticket_text"].lower().split())
        overlap = len(current_words & past_words)
        if overlap > 0:
            scored.append((overlap, t))

    scored.sort(key=lambda x: x[0], reverse=True)
    return {"matches": [t for _, t in scored[:max_results]]}
