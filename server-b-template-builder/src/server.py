#!/usr/bin/env python3
"""
MCP Server B: Template Builder (True MCP Protocol)
Implements Model Context Protocol for dependency validation, problem generation, and project building.

This server exposes:
- Tools: validate_dependencies, generate_leetcode_problems, build_webcontainer_structure
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
server = Server("promora-template-builder")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available tools (MCP protocol).
    """
    return get_tools()


@server.list_resources()
async def handle_list_resources():
    try:
        from resources import RESOURCES
        return RESOURCES
    except Exception:
        return []


@server.read_resource()
async def handle_read_resource(uri: str):
    from resources import read_resource
    return await read_resource(uri)


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


async def run_http_server(port: int):
    """
    Run as a lightweight HTTP REST API for deployment.
    Exposes the same tool handlers over /health, /tools, /call_tool.
    """
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn

    app = FastAPI(title="MCP Server B - Template Builder")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok", "server": "promora-template-builder"}

    @app.get("/tools")
    async def list_tools_endpoint():
        tools = get_tools()
        return {
            "tools": [
                {"name": t.name, "description": t.description, "inputSchema": t.inputSchema}
                for t in tools
            ]
        }

    @app.post("/call_tool")
    async def call_tool_endpoint(request: Request):
        body = await request.json()
        name = body.get("name")
        arguments = body.get("arguments", {})

        if name not in TOOL_HANDLERS:
            return {"error": f"Unknown tool: {name}"}

        try:
            handler = TOOL_HANDLERS[name]
            result = await handler(arguments)
            if result and hasattr(result[0], "text"):
                try:
                    return {"result": json.loads(result[0].text)}
                except Exception:
                    return {"result": result[0].text}
            return {"result": result}
        except Exception as e:
            logger.error(f"Error in tool {name}: {e}", exc_info=True)
            return {"error": str(e)}

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    srv = uvicorn.Server(config)
    await srv.serve()


async def main():
    """
    Run MCP server.
    - MCP_TRANSPORT=http  → HTTP REST API on MCP_PORT (default 8002) — used in deployment
    - MCP_TRANSPORT unset → stdio transport — used for local dev (spawned by backend)
    """
    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport == "http":
        port = int(os.environ.get("MCP_PORT", "8002"))
        logger.info(f"Starting MCP Server B (Template Builder) via HTTP on port {port}...")
        await run_http_server(port)
    else:
        logger.info("Starting MCP Server B (Template Builder) via stdio...")
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )


if __name__ == "__main__":
    asyncio.run(main())

