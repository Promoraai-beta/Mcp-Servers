"""
Agent 6: Watcher Agent
Real-time violation detection for sessions.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import API client for database operations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import DatabaseAPIClient

logger = logging.getLogger(__name__)


async def watch_session(
    session_id: str,
    include_file_operations: bool = True,
    include_terminal_events: bool = True
) -> Dict[str, Any]:
    """
    Real-time violation detection for a session.
    
    Args:
        session_id: Session ID to monitor
        include_file_operations: Include file operation events
        include_terminal_events: Include terminal command events
    
    Returns:
        Dictionary with violations, risk scores, and alerts
    """
    try:
        logger.info(f"Watching session: {session_id}")
        
        # Initialize API client
        db_client = DatabaseAPIClient()
        
        # Get all interactions
        interactions = db_client.get_interactions(session_id)
        
        # Get file operations if requested
        file_operations = []
        if include_file_operations:
            file_operations = db_client.get_file_operations(session_id)
        
        # Get terminal events if requested
        terminal_events = []
        if include_terminal_events:
            terminal_events = db_client.get_terminal_events(session_id)
        
        # Detect violations
        violations = _detect_violations(interactions, file_operations, terminal_events)
        
        # Calculate risk score
        risk_score = _calculate_risk_score(violations, interactions)
        
        # Generate alerts
        alerts = _generate_alerts(violations, risk_score)
        
        # Build timeline
        timeline = _build_timeline(interactions, file_operations, terminal_events)
        
        # Calculate metrics
        metrics = _calculate_metrics(interactions, file_operations, terminal_events)
        
        return {
            "success": True,
            "violations": violations,
            "riskScore": risk_score,
            "alerts": alerts,
            "timeline": timeline,
            "metrics": metrics,
            "confidence": 80,
            "evidence": [v.get("description", "") for v in violations],
            "explanation": f"{len(violations)} violations detected"
        }
    
    except Exception as e:
        logger.error(f"Error watching session: {e}")
        return {
            "success": False,
            "violations": [],
            "riskScore": 0,
            "explanation": f"Error: {str(e)}"
        }


def _detect_violations(
    interactions: List[Dict],
    file_operations: List[Dict],
    terminal_events: List[Dict]
) -> List[Dict[str, Any]]:
    """Detect violations from interactions."""
    violations = []
    
    # Check for large code copies
    copy_events = [i for i in interactions if i.get("event_type") in ["code_copied_from_ai", "code_copied"]]
    paste_events = [i for i in interactions if i.get("event_type") in ["code_pasted_from_ai", "code_pasted"]]
    
    for copy_event in copy_events:
        code_snippet = copy_event.get("code_snippet", "") or ""
        lines = len(code_snippet.split("\n"))
        
        if lines > 50:
            violations.append({
                "severity": "high" if lines > 100 else "medium",
                "type": "large_code_copy",
                "description": f"Copied {lines} lines of code from AI",
                "timestamp": copy_event.get("timestamp", datetime.now()).isoformat() if isinstance(copy_event.get("timestamp"), datetime) else str(copy_event.get("timestamp", ""))
            })
    
    # Check for solution requests
    prompts = [i for i in interactions if i.get("event_type") == "prompt_sent" and i.get("prompt_text")]
    
    red_flag_patterns = [
        "solve.*entire.*problem",
        "write.*complete.*code",
        "give.*full.*solution",
        "do.*whole.*thing"
    ]
    
    import re
    for prompt_event in prompts:
        prompt_text = prompt_event.get("prompt_text", "").lower()
        if any(re.search(pattern, prompt_text) for pattern in red_flag_patterns):
            violations.append({
                "severity": "high",
                "type": "solution_request",
                "description": "Candidate asked AI to solve the entire problem",
                "timestamp": prompt_event.get("timestamp", datetime.now()).isoformat() if isinstance(prompt_event.get("timestamp"), datetime) else str(prompt_event.get("timestamp", ""))
            })
    
    # Check for suspicious file operations
    suspicious_files = ["test", "solution", "answer", "cheat"]
    for file_op in file_operations:
        metadata = file_op.get("metadata", {})
        if isinstance(metadata, str):
            import json
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        
        file_path = metadata.get("filePath", "") or metadata.get("fileName", "")
        if any(sus in file_path.lower() for sus in suspicious_files):
            violations.append({
                "severity": "medium",
                "type": "suspicious_file_operation",
                "description": f"Suspicious file operation: {file_path}",
                "timestamp": file_op.get("timestamp", datetime.now()).isoformat() if isinstance(file_op.get("timestamp"), datetime) else str(file_op.get("timestamp", ""))
            })
    
    return violations


def _calculate_risk_score(violations: List[Dict], interactions: List[Dict]) -> int:
    """Calculate risk score from violations."""
    if not violations:
        return 0
    
    base_score = 0
    for violation in violations:
        severity = violation.get("severity", "low")
        if severity == "high":
            base_score += 30
        elif severity == "medium":
            base_score += 15
        else:
            base_score += 5
    
    # Cap at 100
    return min(100, base_score)


def _generate_alerts(violations: List[Dict], risk_score: int) -> List[Dict[str, Any]]:
    """Generate alerts from violations."""
    alerts = []
    
    if risk_score > 70:
        alerts.append({
            "severity": "critical",
            "message": f"High risk detected: {len(violations)} violations",
            "type": "risk_alert"
        })
    
    high_severity = [v for v in violations if v.get("severity") == "high"]
    if high_severity:
        alerts.append({
            "severity": "high",
            "message": f"{len(high_severity)} high-severity violations detected",
            "type": "violation_alert"
        })
    
    return alerts


def _build_timeline(
    interactions: List[Dict],
    file_operations: List[Dict],
    terminal_events: List[Dict]
) -> List[Dict[str, Any]]:
    """Build timeline of events."""
    timeline = []
    
    # Add interactions
    for event in interactions:
        timeline.append({
            "type": event.get("event_type", ""),
            "timestamp": event.get("timestamp", datetime.now()).isoformat() if isinstance(event.get("timestamp"), datetime) else str(event.get("timestamp", "")),
            "description": _get_event_description(event)
        })
    
    # Add file operations
    for event in file_operations:
        timeline.append({
            "type": event.get("event_type", ""),
            "timestamp": event.get("timestamp", datetime.now()).isoformat() if isinstance(event.get("timestamp"), datetime) else str(event.get("timestamp", "")),
            "description": _get_file_event_description(event)
        })
    
    # Add terminal events
    for event in terminal_events:
        timeline.append({
            "type": event.get("event_type", ""),
            "timestamp": event.get("timestamp", datetime.now()).isoformat() if isinstance(event.get("timestamp"), datetime) else str(event.get("timestamp", "")),
            "description": _get_terminal_event_description(event)
        })
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x.get("timestamp", ""))
    
    return timeline


def _get_event_description(event: Dict) -> str:
    """Get description for an interaction event."""
    event_type = event.get("event_type", "")
    
    if event_type == "prompt_sent":
        prompt_text = event.get("prompt_text", "")
        return f"Asked: {prompt_text[:50]}..." if len(prompt_text) > 50 else f"Asked: {prompt_text}"
    elif event_type == "response_received":
        return "Received AI response"
    elif event_type in ["code_copied_from_ai", "code_copied"]:
        code_snippet = event.get("code_snippet", "")
        lines = len(code_snippet.split("\n"))
        return f"Copied code ({lines} lines)"
    elif event_type == "code_modified":
        return "Modified code"
    else:
        return event_type


def _get_file_event_description(event: Dict) -> str:
    """Get description for a file operation event."""
    event_type = event.get("event_type", "")
    metadata = event.get("metadata", {})
    
    if isinstance(metadata, str):
        import json
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}
    
    file_path = metadata.get("filePath", "") or metadata.get("fileName", "")
    is_directory = metadata.get("isDirectory", False)
    
    if event_type == "file_created":
        return f"Created {'folder' if is_directory else 'file'}: {file_path}"
    elif event_type == "file_modified":
        return f"Modified: {file_path}"
    elif event_type == "file_deleted":
        return f"Deleted {'folder' if is_directory else 'file'}: {file_path}"
    elif event_type == "file_renamed":
        new_name = metadata.get("newName", "")
        return f"Renamed: {file_path} → {new_name}"
    else:
        return event_type


def _get_terminal_event_description(event: Dict) -> str:
    """Get description for a terminal event."""
    event_type = event.get("event_type", "")
    metadata = event.get("metadata", {})
    
    if isinstance(metadata, str):
        import json
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}
    
    if event_type == "terminal_spawned":
        terminal_name = metadata.get("terminalName", "Terminal")
        return f"New terminal: {terminal_name}"
    elif event_type == "command_executed":
        command = metadata.get("command", "command")
        return f"Ran: {command}"
    else:
        return event_type


def _calculate_metrics(
    interactions: List[Dict],
    file_operations: List[Dict],
    terminal_events: List[Dict]
) -> Dict[str, Any]:
    """Calculate metrics from events."""
    return {
        "totalInteractions": len(interactions),
        "totalFileOperations": len(file_operations),
        "totalTerminalEvents": len(terminal_events),
        "fileCreates": len([f for f in file_operations if f.get("event_type") == "file_created"]),
        "fileModifies": len([f for f in file_operations if f.get("event_type") == "file_modified"]),
        "fileDeletes": len([f for f in file_operations if f.get("event_type") == "file_deleted"]),
        "commandsExecuted": len([t for t in terminal_events if t.get("event_type") == "command_executed"])
    }

