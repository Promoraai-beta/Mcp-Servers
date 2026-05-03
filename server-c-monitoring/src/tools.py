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
        ),
        Tool(
            name="score_with_manifest",
            description="Manifest-aware scoring: scores candidate work against the assessment manifest (contract from Server B). Compares final code to known injected bugs, checks expected signals, evaluates behavior, and produces a structured score report per rubric dimension.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sessionId": {
                        "type": "string",
                        "description": "Session ID to score"
                    },
                    "manifest": {
                        "type": "object",
                        "description": "The assessmentManifest object from Server B output. Must include injectedBugIds, expectedSignals, checkpoints, scoringRubric, and skillsMeasured."
                    },
                    "finalFiles": {
                        "type": "object",
                        "description": "Optional dict of {filepath: content} representing the candidate's final code. If not provided, reconstructed from code snapshots."
                    }
                },
                "required": ["sessionId", "manifest"]
            }
        )
    ]

