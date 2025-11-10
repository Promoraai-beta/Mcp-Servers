#!/usr/bin/env python3
"""
MCP Server C: Live Monitoring (True MCP Protocol)
Implements Model Context Protocol for real-time monitoring, code analysis, and violation detection.

This server exposes:
- Tools: watch_session, execute_analysis, flag_sanity_checks
- Uses same agent functions as FastAPI server
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any

# Add src directory to path
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, src_dir)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("ERROR: MCP SDK not installed.")
    print("Install it with: pip install mcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import tools and handlers
from tools import get_tools
from handlers import TOOL_HANDLERS

# Create MCP server
server = Server("promora-monitoring")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available tools (MCP protocol).
    """
    return get_tools()


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle tool calls (MCP protocol).
    """
    try:
        logger.info(f"MCP Tool called: {name}")
        
        if name not in TOOL_HANDLERS:
            raise ValueError(f"Unknown tool: {name}")
        
        handler = TOOL_HANDLERS[name]
        return await handler(arguments)
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]


async def main():
    """
    Run MCP server using stdio transport.
    """
    logger.info("Starting MCP Server C (Live Monitoring) via stdio...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    # Run MCP server
    asyncio.run(main())

