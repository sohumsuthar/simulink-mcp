#!/usr/bin/env python3
"""Simulink MCP Server - Entry point."""
import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import mcp

# Import tool modules to register their tools
import tools.model_management
import tools.inspection
import tools.modification
import tools.simulation

if __name__ == "__main__":
    mcp.run(transport="stdio")
