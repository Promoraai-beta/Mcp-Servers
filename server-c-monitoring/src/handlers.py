"""
MCP Tool Handlers for Server C
Contains the actual tool execution logic
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, List, Dict, Optional

from mcp.types import TextContent

from agents.agent_6_watcher import watch_session
from agents.agent_7_executor import execute_analysis
from agents.agent_8_sanity_flag import flag_sanity_checks
from agents.agent_9_manifest_scorer import score_with_manifest
from utils.api_client import DatabaseAPIClient

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


async def handle_score_with_manifest(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle score_with_manifest tool call."""
    session_id = arguments.get("sessionId")
    manifest = arguments.get("manifest")
    final_files = arguments.get("finalFiles")

    if not session_id:
        raise ValueError("sessionId is required")
    if not manifest:
        raise ValueError("manifest is required")

    logger.info(f"Scoring session {session_id} with manifest (type={manifest.get('assessmentType')})")
    result = await score_with_manifest(session_id, manifest, final_files)

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2, default=str)
    )]


async def handle_full_report(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle full_report tool call.

    Runs Agent 6 (watcher), Agent 7 (executor/behavior), Agent 8 (sanity flags),
    fetches the session manifest, and — if a manifest is available — runs Agent 9
    (manifest scorer). Combines everything into a single comprehensive report.
    """
    session_id = arguments.get("sessionId")
    include_manifest = arguments.get("includeManifest", True)

    if not session_id:
        raise ValueError("sessionId is required")

    logger.info(f"Generating full report for session: {session_id}")

    # ── Run agents 6, 7, 8 concurrently ────────────────────────────────────
    import asyncio

    agent6_task = asyncio.create_task(watch_session(session_id, True, True))
    agent7_task = asyncio.create_task(execute_analysis(session_id, None))
    agent8_task = asyncio.create_task(flag_sanity_checks(session_id, None))

    agent6_result, agent7_result, agent8_result = await asyncio.gather(
        agent6_task, agent7_task, agent8_task,
        return_exceptions=True,
    )

    # Normalise exceptions to error dicts so the report is always complete
    def _safe(r, label: str):
        if isinstance(r, Exception):
            logger.error(f"[full_report] {label} failed: {r}", exc_info=r)
            return {"error": str(r), "agent": label}
        return r

    agent6_result = _safe(agent6_result, "agent6_watcher")
    agent7_result = _safe(agent7_result, "agent7_executor")
    agent8_result = _safe(agent8_result, "agent8_sanity_flag")

    # ── Fetch manifest and run Agent 9 ──────────────────────────────────────
    manifest = None
    agent9_result = None

    if include_manifest:
        try:
            db_client = DatabaseAPIClient()
            manifest = db_client.get_manifest(session_id)
        except Exception as e:
            logger.warning(f"[full_report] Could not fetch manifest: {e}")
            manifest = None

        if manifest:
            try:
                agent9_result = await score_with_manifest(session_id, manifest, None)
            except Exception as e:
                logger.error(f"[full_report] agent9 failed: {e}", exc_info=True)
                agent9_result = {"error": str(e), "agent": "agent9_manifest_scorer"}

    # ── Compute weighted overall score ──────────────────────────────────────
    scores: List[float] = []

    def _extract_score(result, key: str, scale: float = 1.0) -> Optional[float]:
        if isinstance(result, dict) and key in result:
            try:
                return float(result[key]) * scale
            except (TypeError, ValueError):
                pass
        return None

    # Agent 7 typically returns a behaviorScore 0-100
    s7 = _extract_score(agent7_result, "behaviorScore")
    if s7 is not None:
        scores.append(s7)

    # Agent 9 returns overallScore 0-100
    if agent9_result and not isinstance(agent9_result, Exception):
        s9 = _extract_score(agent9_result, "overallScore")
        if s9 is not None:
            scores.append(s9)

    overall_score = round(sum(scores) / len(scores), 1) if scores else None

    # ── Assemble combined report ────────────────────────────────────────────
    report = {
        "sessionId": session_id,
        "agents": {
            "codeQuality": agent6_result,
            "behaviorScore": agent7_result,
            "sanityFlags": agent8_result,
            "manifestScore": agent9_result if manifest else None,
        },
        "summary": {
            "overallScore": overall_score,
            "hasManifest": bool(manifest),
            "completedAt": datetime.now(timezone.utc).isoformat(),
        },
    }

    return [TextContent(
        type="text",
        text=json.dumps(report, indent=2, default=str)
    )]


# Tool handler mapping
TOOL_HANDLERS = {
    "watch_session": handle_watch_session,
    "execute_analysis": handle_execute_analysis,
    "flag_sanity_checks": handle_flag_sanity_checks,
    "score_with_manifest": handle_score_with_manifest,
    "full_report": handle_full_report,
}

