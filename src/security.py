"""
Security: structural gating for diagnostic actions.

Demonstrates two ideas from the course's security material, scoped down to
something appropriate for this project's size:

1. Zero ambient authority: the agent never gets a human's full credentials.
   It only ever gets the narrow inputs a tool call needs (a hostname, a
   service name) - never a session token, password, or API key. Secrets
   live only in environment variables (see .env.example), never in agent
   context or code.

2. Structural gating: a fast, deterministic allow-list check that runs
   BEFORE a diagnostic action, independent of what the LLM "decides" to do.
   This is intentionally dumb and rule-based - the point is that it cannot
   be argued with or prompt-injected, unlike an instruction in a system prompt.
"""

# In a real deployment this would be loaded from a config file or a
# service registry, not hardcoded - kept simple here for demo purposes.
ALLOWED_SERVICE_PREFIXES = ("vpn-", "print-", "auth-", "file-", "db-")
ALLOWED_HOST_SUFFIXES = (".local", ".internal", "01", "02", "03")


def is_service_allowed(service_name: str) -> bool:
    """Checks a service name against the allow-list before it can be queried.

    This runs independently of the LLM's reasoning - even if the model is
    tricked (e.g. via a prompt injection hidden in a ticket description)
    into asking about a service outside this list, the check below still
    blocks it deterministically.
    """
    return service_name.lower().startswith(ALLOWED_SERVICE_PREFIXES)


def is_host_allowed(host: str) -> bool:
    """Checks a hostname against a simple allow-list pattern.

    Restricts diagnostics to internal-looking hosts only, so the agent
    can never be steered into probing arbitrary external addresses.
    """
    return host.lower().endswith(ALLOWED_HOST_SUFFIXES)
