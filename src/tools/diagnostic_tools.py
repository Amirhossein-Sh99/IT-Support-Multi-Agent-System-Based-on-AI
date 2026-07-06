"""
Simulated IT diagnostic tools.

These are deliberately simplified simulations (no real network calls) so the
agent can be demoed safely and deterministically. In a production version,
these would call real system utilities (subprocess to `ping`, `traceroute`,
reading actual log files, querying a ticketing system API, etc.).
"""

import random

from src.security import is_host_allowed, is_service_allowed


def check_network_connectivity(host: str) -> dict:
    """Simulates a ping/connectivity check to a host.

    Args:
        host: The hostname or IP address to check.

    Returns:
        A dict with keys: host, reachable (bool), latency_ms (float), packet_loss_pct (float).
    """
    if not is_host_allowed(host):
        return {"host": host, "error": "Host not in allow-list; diagnostics refused."}

    # Deterministic-ish simulation based on the host string so demos are repeatable.
    seed = sum(ord(c) for c in host)
    random.seed(seed)
    reachable = random.random() > 0.25
    latency = round(random.uniform(5, 250), 1) if reachable else None
    packet_loss = 0.0 if reachable else round(random.uniform(50, 100), 1)

    return {
        "host": host,
        "reachable": reachable,
        "latency_ms": latency,
        "packet_loss_pct": packet_loss,
    }


def run_traceroute(host: str) -> dict:
    """Simulates a traceroute to a host, returning hop-by-hop latency.

    Args:
        host: The hostname or IP address to trace.

    Returns:
        A dict with keys: host, hops (list of {hop, address, latency_ms}).
    """
    seed = sum(ord(c) for c in host)
    random.seed(seed + 1)
    num_hops = random.randint(3, 8)
    hops = []
    for i in range(1, num_hops + 1):
        hops.append({
            "hop": i,
            "address": f"10.0.{i}.1",
            "latency_ms": round(random.uniform(1, 40) * i, 1),
        })
    return {"host": host, "hops": hops}


def parse_system_logs(keyword: str, max_results: int = 5) -> dict:
    """Simulates searching system logs for a keyword (e.g. an error code).

    Args:
        keyword: The search term, e.g. 'DNS timeout' or error code.
        max_results: Maximum number of matching log lines to return.

    Returns:
        A dict with keys: keyword, matches (list of log line strings).
    """
    sample_logs = [
        "2026-07-04 09:12:03 WARN dns resolver timeout for host printserver01",
        "2026-07-04 09:12:05 ERROR DHCP lease renewal failed on eth0",
        "2026-07-04 09:13:44 INFO VPN tunnel re-established after drop",
        "2026-07-04 09:14:01 ERROR disk usage 96% on /var partition",
        "2026-07-04 09:15:22 WARN authentication retry limit reached for user jsmith",
        "2026-07-04 09:16:09 ERROR DNS timeout resolving internal.company.local",
    ]
    matches = [line for line in sample_logs if keyword.lower() in line.lower()]
    return {"keyword": keyword, "matches": matches[:max_results]}


def check_service_status(service_name: str) -> dict:
    """Simulates checking whether a system service is running.

    Args:
        service_name: Name of the service, e.g. 'print-spooler', 'vpn-client'.

    Returns:
        A dict with keys: service_name, status ('running'|'stopped'|'error').
    """
    if not is_service_allowed(service_name):
        return {"service_name": service_name, "error": "Service not in allow-list; check refused."}

    seed = sum(ord(c) for c in service_name)
    random.seed(seed + 2)
    status = random.choice(["running", "running", "stopped", "error"])
    return {"service_name": service_name, "status": status}
