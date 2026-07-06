"""
Diagnostics MCP Server

Exposes the simulated IT diagnostic checks as an MCP (Model Context Protocol)
server, so the Diagnostics Agent connects to them the same way it would
connect to any external tool provider — over a standard protocol, not a
hardcoded Python import.

This demonstrates the "MCP Server" concept from the course: instead of the
agent calling Python functions directly, it discovers and calls tools through
a standardized transport (stdio here, for local development).

Run standalone for testing:
    python mcp_server/diagnostics_server.py
"""

from mcp.server.fastmcp import FastMCP

import sys
import os

# When ADK launches this file as a subprocess, Python only puts this
# script's own folder (mcp_server/) on sys.path - not the project root -
# so the "src" package below would otherwise fail to import. This adds
# the project root explicitly, regardless of the caller's working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.diagnostic_tools import (
    check_network_connectivity,
    run_traceroute,
    parse_system_logs,
    check_service_status,
)

mcp = FastMCP("it-diagnostics")


@mcp.tool()
def network_check(host: str) -> dict:
    """Checks connectivity to a host (simulated ping).

    Args:
        host: Hostname or IP address to check.
    """
    return check_network_connectivity(host)


@mcp.tool()
def traceroute(host: str) -> dict:
    """Runs a simulated traceroute to a host, returning hop latencies.

    Args:
        host: Hostname or IP address to trace.
    """
    return run_traceroute(host)


@mcp.tool()
def search_logs(keyword: str, max_results: int = 5) -> dict:
    """Searches simulated system logs for a keyword or error pattern.

    Args:
        keyword: Search term, e.g. an error code or phrase.
        max_results: Maximum number of matching lines to return.
    """
    return parse_system_logs(keyword, max_results)


@mcp.tool()
def service_status(service_name: str) -> dict:
    """Checks whether a named service is running (simulated).

    Args:
        service_name: The service to check, e.g. 'vpn-client'.
    """
    return check_service_status(service_name)


if __name__ == "__main__":
    # Runs over stdio transport - the agent process launches this as a
    # subprocess and communicates over stdin/stdout, per MCP's stdio spec.
    mcp.run(transport="stdio")
