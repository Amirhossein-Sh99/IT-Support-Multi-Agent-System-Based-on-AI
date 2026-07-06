# Worked Examples

## Example 1: VPN connectivity issue

**Ticket:** "I can't connect to the office VPN since this morning."

1. `find_similar_tickets("can't connect to VPN")` → finds a past ticket:
   root cause was "VPN client service stopped after update", fix was
   "restart the VPN client service".
2. Verify with `service_status("vpn-client")` → confirms status is "stopped".
3. Root cause confirmed. No need to also run `network_check` or `traceroute`
   since the service-level check already gives a clear signal.

## Example 2: Intermittent connection drops

**Ticket:** "My connection to the fileserver keeps dropping every few minutes."

1. `find_similar_tickets(...)` → no close match found.
2. Category is "network", so start with `network_check("fileserver01")`.
3. Result shows high packet loss but the host is technically reachable —
   inconclusive on its own, so escalate to `traceroute("fileserver01")` to
   see which hop is introducing latency.
4. Root cause: a specific hop shows abnormal latency, pointing to a
   switch/routing issue rather than the fileserver itself.
