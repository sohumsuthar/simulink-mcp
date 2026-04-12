"""Simulink MCP Server — give AI assistants direct access to MATLAB Simulink."""

from simulink_mcp.app import mcp

# Register tool modules
import simulink_mcp.tools.model_management  # noqa: F401
import simulink_mcp.tools.inspection  # noqa: F401
import simulink_mcp.tools.modification  # noqa: F401
import simulink_mcp.tools.simulation  # noqa: F401


def main():
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")
