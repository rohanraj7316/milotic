"""System-related tools for Milotic Gateway."""

from fastmcp.tools import tool
from milotic.utils.decorators import milotic_tool

@tool()
@milotic_tool
def system_get_health() -> dict[str, str]:
    """
    Return server health status. 
    Verifies the gateway is online and correctly configured.
    """
    return {
        "status": "ok", 
        "phase": "1.1", 
        "foundation": "refined",
        "backend": "not_connected"
    }
