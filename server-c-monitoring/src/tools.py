"""
MCP Tools Definitions for Server C
Contains all tool schemas and descriptions
"""

from mcp.types import Tool


def get_tools() -> list[Tool]:
    """
    Return list of available tools for Server C.
    """
    return [
        Tool(
            name="watch_session",
            description="Real-time violation detection for a session. Tracks file operations, terminal commands, and detects violations. Returns violations, risk scores, and alerts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sessionId": {
                        "type": "string",
                        "description": "Session ID to monitor"
                    },
                    "includeFileOperations": {
                        "type": "boolean",
                        "description": "Include file operations in analysis",
                        "default": True
                    },
                    "includeTerminalEvents": {
                        "type": "boolean",
                        "description": "Include terminal events in analysis",
                        "default": True
                    }
                },
                "required": ["sessionId"]
            }
        ),
        Tool(
            name="execute_analysis",
            description="Executes code analysis for a session. Extracts patterns, quality metrics, and code quality scores. Returns comprehensive analysis results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sessionId": {
                        "type": "string",
                        "description": "Session ID to analyze"
                    },
                    "code": {
                        "type": "string",
                        "description": "Optional code to analyze directly"
                    }
                },
                "required": ["sessionId"]
            }
        ),
        Tool(
            name="flag_sanity_checks",
            description="Flags suspicious behavior and performs risk assessment. Detects anomalies, plagiarism patterns, and generates risk flags with sanity checks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sessionId": {
                        "type": "string",
                        "description": "Session ID to check"
                    },
                    "events": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Optional events to analyze (if not provided, fetched from database)"
                    }
                },
                "required": ["sessionId"]
            }
        )
    ]

