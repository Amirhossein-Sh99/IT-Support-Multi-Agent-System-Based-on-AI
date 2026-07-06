---
name: it-diagnostics-playbook
description: Use when diagnosing an IT support ticket that has already been triaged (category + urgency known). Provides the procedural order of operations for investigating network, hardware, software, or access issues before proposing a fix.
---

# IT Diagnostics Playbook

This skill captures the *procedure* an experienced helpdesk technician follows —
not the tools themselves (those come from the MCP server), but the order and
judgment calls around using them. This is the "know-how" layer described in
the course: MCP gives an agent reach, a skill gives it know-how.

## Step 1 — Check memory first

Before running any live diagnostic, search for similar past tickets
(`find_similar_tickets`). If a close match exists with a known root cause and
fix, treat it as a strong prior — but still verify with at least one live
check before finalizing, since past fixes can go stale.

## Step 2 — Match category to tool

| Triage category | Start with |
|---|---|
| network | `network_check`, then `traceroute` if unreachable |
| software | `service_status` on the named application/service |
| access | `search_logs` for authentication-related keywords |
| hardware | `search_logs` for the device/driver name |

## Step 3 — Escalate tool usage only if the first check is inconclusive

Don't call every tool "just in case" — this wastes tokens and context. Only
reach for a second tool if the first one didn't produce a clear signal (e.g.
`network_check` says reachable, but the user still reports being unable to
connect — that's when you'd check `service_status` on the client next).

## Step 4 — State root cause and fix together

Never report a root cause without an accompanying concrete, actionable fix.
"The VPN service is stopped" is a diagnosis, not a resolution — pair it with
"restart the VPN client service" or the appropriate next step.

## References

See `scripts/example_traces.md` for two worked examples of this playbook applied
to real ticket text.
