"""
Agent 8: Sanity Flag Agent
Advanced violation detection and risk assessment.
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


async def flag_sanity_checks(session_id: str, events: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Flag suspicious behavior and perform risk assessment.
    
    Args:
        session_id: Session ID to check
        events: Optional recent events to analyze
    
    Returns:
        Dictionary with risk flags, sanity checks, and analysis
    """
    try:
        logger.info(f"Flagging sanity checks for session: {session_id}")
        
        # Initialize API client
        db_client = DatabaseAPIClient()
        
        # Get events if not provided
        if not events:
            interactions = db_client.get_interactions(session_id)
            file_operations = db_client.get_file_operations(session_id)
            terminal_events = db_client.get_terminal_events(session_id)
            events = interactions + file_operations + terminal_events
        
        # Get submissions for plagiarism analysis
        submissions = db_client.get_submissions(session_id)
        
        # Detect violations
        violations = _detect_violations(events)
        
        # Calculate risk score
        risk_score = _calculate_risk_score(violations, events)
        
        # Detect red flags
        red_flags = _detect_red_flags(events, submissions)
        
        # Detect anomalies
        anomalies = _detect_anomalies(events)
        
        # Analyze plagiarism
        plagiarism_analysis = _analyze_plagiarism(submissions, events)
        
        # Generate sanity checks
        sanity_checks = _generate_sanity_checks(violations, red_flags, anomalies)
        
        return {
            "success": True,
            "violations": violations,
            "riskScore": risk_score,
            "redFlags": red_flags,
            "anomalies": anomalies,
            "plagiarismAnalysis": plagiarism_analysis,
            "sanityChecks": sanity_checks,
            "confidence": 85,
            "explanation": f"Risk assessment completed: {len(violations)} violations, {len(red_flags)} red flags"
        }
    
    except Exception as e:
        logger.error(f"Error flagging sanity checks: {e}")
        return {
            "success": False,
            "explanation": f"Error: {str(e)}"
        }


def _detect_violations(events: List[Dict]) -> List[Dict[str, Any]]:
    """Detect violations from events."""
    violations = []
    
    # Check for solution request patterns
    prompts = [e for e in events if e.get("event_type") == "prompt_sent" and e.get("prompt_text")]
    
    import re
    solution_patterns = [
        r"solve.*entire.*problem",
        r"write.*complete.*solution",
        r"give.*full.*code",
        r"do.*whole.*thing",
        r"complete.*for.*me"
    ]
    
    for prompt in prompts:
        prompt_text = prompt.get("prompt_text", "").lower()
        if any(re.search(pattern, prompt_text) for pattern in solution_patterns):
            violations.append({
                "severity": "high",
                "type": "solution_request_pattern",
                "description": "Candidate requested complete solution",
                "timestamp": prompt.get("timestamp", datetime.now()).isoformat() if isinstance(prompt.get("timestamp"), datetime) else str(prompt.get("timestamp", ""))
            })
    
    # Check for excessive code copying
    copy_events = [e for e in events if e.get("event_type") in ["code_copied_from_ai", "code_copied"]]
    
    if len(copy_events) > 5:
        violations.append({
            "severity": "high",
            "type": "excessive_copying",
            "description": f"Excessive code copying: {len(copy_events)} copy events",
            "timestamp": datetime.now().isoformat()
        })
    
    # Check for suspicious timing (too fast completion)
    modifications = [e for e in events if e.get("event_type") == "code_modified"]
    if len(modifications) < 3 and len(prompts) > 10:
        violations.append({
            "severity": "medium",
            "type": "suspicious_timing",
            "description": "Very few modifications compared to prompts (potential copy-paste)",
            "timestamp": datetime.now().isoformat()
        })
    
    return violations


def _calculate_risk_score(violations: List[Dict], events: List[Dict]) -> int:
    """Calculate comprehensive risk score."""
    base_score = 0
    
    # Violation-based scoring
    for violation in violations:
        severity = violation.get("severity", "low")
        if severity == "high":
            base_score += 30
        elif severity == "medium":
            base_score += 15
        else:
            base_score += 5
    
    # Event pattern scoring
    prompts = [e for e in events if e.get("event_type") == "prompt_sent"]
    copies = [e for e in events if e.get("event_type") in ["code_copied_from_ai", "code_copied"]]
    modifications = [e for e in events if e.get("event_type") == "code_modified"]
    
    # High copy-to-modification ratio = risk
    if modifications and copies:
        copy_mod_ratio = len(copies) / len(modifications)
        if copy_mod_ratio > 2:
            base_score += 20
    
    # Very high prompt frequency = risk
    if len(prompts) > 20:
        base_score += 15
    
    # Cap at 100
    return min(100, base_score)


def _detect_red_flags(events: List[Dict], submissions: List[Dict]) -> List[Dict[str, Any]]:
    """Detect red flags indicating cheating."""
    red_flags = []
    
    # Flag 1: Perfect solution with no modifications
    if submissions:
        perfect_submissions = [s for s in submissions if s.get("score", 0) == 100]
        modifications = [e for e in events if e.get("event_type") == "code_modified"]
        
        if perfect_submissions and len(modifications) < 3:
            red_flags.append({
                "type": "perfect_solution_no_modifications",
                "description": "Perfect solution with minimal code modifications",
                "severity": "high"
            })
    
    # Flag 2: Rapid code completion
    if len(events) > 0:
        first_event = min(events, key=lambda e: e.get("timestamp", datetime.now()))
        last_event = max(events, key=lambda e: e.get("timestamp", datetime.now()))
        
        time_diff = _time_diff(first_event.get("timestamp"), last_event.get("timestamp"))
        if time_diff and time_diff < 300:  # Less than 5 minutes
            modifications = [e for e in events if e.get("event_type") == "code_modified"]
            if len(modifications) > 10:
                red_flags.append({
                    "type": "rapid_completion",
                    "description": "Rapid code completion with many modifications",
                    "severity": "medium"
                })
    
    # Flag 3: No code modifications, only copies
    copies = [e for e in events if e.get("event_type") in ["code_copied_from_ai", "code_copied"]]
    modifications = [e for e in events if e.get("event_type") == "code_modified"]
    
    if copies and len(modifications) == 0:
        red_flags.append({
            "type": "no_modifications_only_copies",
            "description": "No code modifications, only copy-paste operations",
            "severity": "high"
        })
    
    return red_flags


def _detect_anomalies(events: List[Dict]) -> List[Dict[str, Any]]:
    """Detect anomalies in event patterns."""
    anomalies = []
    
    if len(events) < 2:
        return anomalies
    
    # Analyze timing gaps
    sorted_events = sorted(events, key=lambda e: e.get("timestamp", datetime.now()))
    gaps = []
    
    for i in range(1, len(sorted_events)):
        gap = _time_diff(sorted_events[i-1].get("timestamp"), sorted_events[i].get("timestamp"))
        if gap:
            gaps.append(gap)
    
    if gaps:
        avg_gap = sum(gaps) / len(gaps)
        # Very small gaps (rapid fire) or very large gaps (inactivity)
        if avg_gap < 5:  # Less than 5 seconds between events
            anomalies.append({
                "type": "rapid_fire_events",
                "description": "Events occurring in rapid succession",
                "severity": "medium"
            })
        elif avg_gap > 3600:  # More than 1 hour between events
            anomalies.append({
                "type": "long_inactivity",
                "description": "Long periods of inactivity detected",
                "severity": "low"
            })
    
    return anomalies


def _analyze_plagiarism(submissions: List[Dict], events: List[Dict]) -> Dict[str, Any]:
    """Analyze plagiarism patterns."""
    analysis = {
        "suspicious": False,
        "patterns": [],
        "confidence": 0
    }
    
    # Check for identical submissions
    if len(submissions) > 1:
        codes = [s.get("code", "") for s in submissions if s.get("code")]
        if len(set(codes)) < len(codes):
            analysis["suspicious"] = True
            analysis["patterns"].append("identical_submissions")
            analysis["confidence"] = 80
    
    # Check for code that matches AI responses exactly
    copies = [e for e in events if e.get("event_type") in ["code_copied_from_ai", "code_copied"]]
    responses = [e for e in events if e.get("event_type") == "response_received"]
    
    if copies and responses:
        # Check if copied code matches any AI response
        for copy_event in copies:
            copied_code = copy_event.get("code_snippet", "")
            for response in responses:
                response_text = response.get("response_text", "")
                if copied_code and response_text and copied_code in response_text:
                    analysis["suspicious"] = True
                    analysis["patterns"].append("code_matches_ai_response")
                    analysis["confidence"] = max(analysis["confidence"], 70)
                    break
    
    return analysis


def _generate_sanity_checks(
    violations: List[Dict],
    red_flags: List[Dict],
    anomalies: List[Dict]
) -> List[Dict[str, Any]]:
    """Generate sanity checks."""
    checks = []
    
    # Check 1: Violation count
    if len(violations) > 5:
        checks.append({
            "check": "violation_count",
            "status": "failed",
            "message": f"Too many violations: {len(violations)}"
        })
    else:
        checks.append({
            "check": "violation_count",
            "status": "passed",
            "message": f"Violation count acceptable: {len(violations)}"
        })
    
    # Check 2: Red flags
    if red_flags:
        high_severity_flags = [f for f in red_flags if f.get("severity") == "high"]
        if high_severity_flags:
            checks.append({
                "check": "red_flags",
                "status": "failed",
                "message": f"{len(high_severity_flags)} high-severity red flags detected"
            })
        else:
            checks.append({
                "check": "red_flags",
                "status": "warning",
                "message": f"{len(red_flags)} red flags detected"
            })
    else:
        checks.append({
            "check": "red_flags",
            "status": "passed",
            "message": "No red flags detected"
        })
    
    # Check 3: Anomalies
    if anomalies:
        checks.append({
            "check": "anomalies",
            "status": "warning",
            "message": f"{len(anomalies)} anomalies detected"
        })
    else:
        checks.append({
            "check": "anomalies",
            "status": "passed",
            "message": "No anomalies detected"
        })
    
    return checks


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

