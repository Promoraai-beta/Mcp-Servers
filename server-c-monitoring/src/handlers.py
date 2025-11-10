"""
MCP Tool Handlers for Server C
Contains the actual tool execution logic
"""

import json
import logging
from typing import Any, List, Dict, Optional

from mcp.types import TextContent

from agents.agent_6_watcher import watch_session
from agents.agent_7_executor import execute_analysis
from agents.agent_8_sanity_flag import flag_sanity_checks

logger = logging.getLogger(__name__)


async def handle_watch_session(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle watch_session tool call."""
    session_id = arguments.get("sessionId")
    include_file_ops = arguments.get("includeFileOperations", True)
    include_terminal = arguments.get("includeTerminalEvents", True)
    
    if not session_id:
        raise ValueError("sessionId is required")
    
    logger.info(f"Watching session: {session_id}")
    result = await watch_session(session_id, include_file_ops, include_terminal)
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2, default=str)
    )]


async def handle_execute_analysis(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle execute_analysis tool call."""
    session_id = arguments.get("sessionId")
    code = arguments.get("code")
    
    if not session_id:
        raise ValueError("sessionId is required")
    
    logger.info(f"Executing analysis for session: {session_id}")
    result = await execute_analysis(session_id, code)
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2, default=str)
    )]


async def handle_flag_sanity_checks(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle flag_sanity_checks tool call."""
    session_id = arguments.get("sessionId")
    events = arguments.get("events")
    
    if not session_id:
        raise ValueError("sessionId is required")
    
    logger.info(f"Flagging sanity checks for session: {session_id}")
    result = await flag_sanity_checks(session_id, events)
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2, default=str)
    )]


# Tool handler mapping
TOOL_HANDLERS = {
    "watch_session": handle_watch_session,
    "execute_analysis": handle_execute_analysis,
    "flag_sanity_checks": handle_flag_sanity_checks
}

