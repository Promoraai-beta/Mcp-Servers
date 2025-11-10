"""
Agent 7: Executor Agent
Executes code analysis and extracts patterns.
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


async def execute_analysis(session_id: str, code: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute code analysis for a session.
    
    Args:
        session_id: Session ID to analyze
        code: Optional code snippet to analyze directly
    
    Returns:
        Dictionary with code quality analysis results
    """
    try:
        logger.info(f"Executing analysis for session: {session_id}")
        
        # Initialize API client
        db_client = DatabaseAPIClient()
        
        # Get code if not provided
        if not code:
            snapshots = db_client.get_code_snapshots(session_id)
            if snapshots:
                code = snapshots[-1].get("code", "")
        
        # Get interactions for context
        interactions = db_client.get_interactions(session_id)
        
        # Analyze code quality
        code_quality = _assess_code_quality(code) if code else {}
        
        # Extract patterns
        patterns = _extract_patterns(interactions)
        
        # Analyze code integration
        code_integration = _analyze_code_integration(interactions)
        
        # Calculate behavior score
        behavior_score = _calculate_behavior_score(interactions)
        
        # Assess skills
        skills = _assess_skills(interactions, code)
        
        return {
            "success": True,
            "codeQuality": code_quality,
            "patterns": patterns,
            "codeIntegration": code_integration,
            "behaviorScore": behavior_score,
            "skills": skills,
            "confidence": 75,
            "explanation": "Code analysis completed"
        }
    
    except Exception as e:
        logger.error(f"Error executing analysis: {e}")
        return {
            "success": False,
            "explanation": f"Error: {str(e)}"
        }


def _assess_code_quality(code: str) -> Dict[str, Any]:
    """Assess code quality metrics."""
    if not code:
        return {}
    
    lines = code.split("\n")
    total_lines = len(lines)
    non_empty_lines = len([l for l in lines if l.strip()])
    comments = len([l for l in lines if l.strip().startswith("#") or l.strip().startswith("//")])
    
    # Simple complexity estimate (based on indentation depth)
    max_indent = 0
    for line in lines:
        indent = len(line) - len(line.lstrip())
        max_indent = max(max_indent, indent)
    
    complexity = "low" if max_indent < 8 else "medium" if max_indent < 16 else "high"
    
    return {
        "totalLines": total_lines,
        "nonEmptyLines": non_empty_lines,
        "comments": comments,
        "commentRatio": comments / non_empty_lines if non_empty_lines > 0 else 0,
        "complexity": complexity,
        "maxIndentation": max_indent
    }


def _extract_patterns(interactions: List[Dict]) -> Dict[str, Any]:
    """Extract patterns from interactions."""
    patterns = {
        "copyPastePatterns": [],
        "timingPatterns": {},
        "promptPatterns": {}
    }
    
    # Detect copy-paste patterns
    copy_events = [i for i in interactions if i.get("event_type") in ["code_copied_from_ai", "code_copied"]]
    paste_events = [i for i in interactions if i.get("event_type") in ["code_pasted_from_ai", "code_pasted"]]
    
    for copy_event in copy_events:
        paste = next((p for p in paste_events if _events_close_in_time(copy_event, p)), None)
        if paste:
            patterns["copyPastePatterns"].append({
                "copyTimestamp": copy_event.get("timestamp", ""),
                "pasteTimestamp": paste.get("timestamp", ""),
                "timeDiff": _time_diff(copy_event.get("timestamp"), paste.get("timestamp"))
            })
    
    # Analyze timing patterns
    if len(interactions) >= 2:
        gaps = []
        for i in range(1, len(interactions)):
            gap = _time_diff(interactions[i-1].get("timestamp"), interactions[i].get("timestamp"))
            if gap:
                gaps.append(gap)
        
        if gaps:
            patterns["timingPatterns"] = {
                "averageGap": sum(gaps) / len(gaps),
                "medianGap": sorted(gaps)[len(gaps) // 2],
                "totalEvents": len(interactions)
            }
    
    # Categorize prompts
    prompts = [i for i in interactions if i.get("event_type") == "prompt_sent"]
    pattern_categories = {
        "solution_request": 0,
        "explanation_request": 0,
        "code_review": 0,
        "other": 0
    }
    
    import re
    for prompt in prompts:
        prompt_text = prompt.get("prompt_text", "").lower()
        if re.search(r"solve|complete|write.*code|implement", prompt_text):
            pattern_categories["solution_request"] += 1
        elif re.search(r"explain|why|how.*work", prompt_text):
            pattern_categories["explanation_request"] += 1
        elif re.search(r"review|check|improve", prompt_text):
            pattern_categories["code_review"] += 1
        else:
            pattern_categories["other"] += 1
    
    patterns["promptPatterns"] = pattern_categories
    
    return patterns


def _analyze_code_integration(interactions: List[Dict]) -> Dict[str, Any]:
    """Analyze how code was integrated."""
    modifications = [i for i in interactions if i.get("event_type") == "code_modified"]
    copies = [i for i in interactions if i.get("event_type") in ["code_copied_from_ai", "code_copied"]]
    
    return {
        "modifications": len(modifications),
        "copies": len(copies),
        "modificationRatio": len(modifications) / len(copies) if copies else 0,
        "integrationQuality": "good" if len(modifications) > len(copies) else "poor"
    }


def _calculate_behavior_score(interactions: List[Dict]) -> int:
    """Calculate behavior score (0-100)."""
    if not interactions:
        return 50
    
    prompts = [i for i in interactions if i.get("event_type") == "prompt_sent"]
    modifications = [i for i in interactions if i.get("event_type") == "code_modified"]
    
    # More modifications relative to prompts = better behavior
    if prompts:
        ratio = len(modifications) / len(prompts)
        score = min(100, int(ratio * 50 + 50))  # Scale to 50-100
    else:
        score = 50
    
    return score


def _assess_skills(interactions: List[Dict], code: Optional[str]) -> Dict[str, Any]:
    """Assess candidate skills from interactions and code."""
    skills = {
        "problemSolving": "medium",
        "codeQuality": "medium",
        "independence": "medium"
    }
    
    # Assess independence based on prompt frequency
    prompts = [i for i in interactions if i.get("event_type") == "prompt_sent"]
    modifications = [i for i in interactions if i.get("event_type") == "code_modified"]
    
    if prompts and modifications:
        independence_ratio = len(modifications) / len(prompts)
        if independence_ratio > 2:
            skills["independence"] = "high"
        elif independence_ratio < 0.5:
            skills["independence"] = "low"
    
    # Assess code quality from code if available
    if code:
        lines = code.split("\n")
        if len(lines) > 50:
            skills["codeQuality"] = "high"
        elif len(lines) < 10:
            skills["codeQuality"] = "low"
    
    return skills


def _events_close_in_time(event1: Dict, event2: Dict, threshold_seconds: int = 30) -> bool:
    """Check if two events are close in time."""
    time_diff = _time_diff(event1.get("timestamp"), event2.get("timestamp"))
    return time_diff is not None and 0 < time_diff < threshold_seconds


def _time_diff(timestamp1: Any, timestamp2: Any) -> Optional[float]:
    """Calculate time difference in seconds."""
    try:
        if isinstance(timestamp1, str):
            from dateutil.parser import parse
            timestamp1 = parse(timestamp1)
        if isinstance(timestamp2, str):
            from dateutil.parser import parse
            timestamp2 = parse(timestamp2)
        
        if isinstance(timestamp1, datetime) and isinstance(timestamp2, datetime):
            diff = (timestamp2 - timestamp1).total_seconds()
            return diff if diff > 0 else None
    except:
        pass
    return None

