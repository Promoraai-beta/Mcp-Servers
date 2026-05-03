"""
Agent 7: Executor Agent
Executes code analysis and extracts patterns.

FIELD NOTE: Prisma returns camelCase fields (eventType, promptText, etc.).
All lookups use _evt() helper that checks both camelCase and snake_case.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import DatabaseAPIClient

logger = logging.getLogger(__name__)


# ── field helpers ─────────────────────────────────────────────────────────────

def _evt(interaction: Dict) -> str:
    """Return the event type regardless of camelCase vs snake_case."""
    return interaction.get("eventType") or interaction.get("event_type") or ""

def _prompt_text(interaction: Dict) -> str:
    """Return prompt text regardless of field naming."""
    return interaction.get("promptText") or interaction.get("prompt_text") or ""

def _ts(interaction: Dict):
    """Return timestamp value."""
    return interaction.get("timestamp") or interaction.get("created_at")


# ── main entry point ──────────────────────────────────────────────────────────

async def execute_analysis(session_id: str, code: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute code analysis for a session.
    Returns behaviorScore 0-100 based on real interaction signals.
    """
    try:
        logger.info(f"Executing analysis for session: {session_id}")

        db_client = DatabaseAPIClient()

        # Get code from latest snapshot if not provided
        if not code:
            snapshots = db_client.get_code_snapshots(session_id)
            if snapshots:
                code = snapshots[-1].get("code", "")

        # Get all interactions
        interactions = db_client.get_interactions(session_id)
        logger.info(f"Agent 7: loaded {len(interactions)} interactions for session {session_id}")

        # Log unique event types seen (helps debug missing events)
        event_types_seen = list({_evt(i) for i in interactions if _evt(i)})
        logger.info(f"Agent 7: event types found: {event_types_seen}")

        code_quality    = _assess_code_quality(code) if code else {}
        patterns        = _extract_patterns(interactions)
        code_integration = _analyze_code_integration(interactions)
        behavior_score  = _calculate_behavior_score(interactions)
        skills          = _assess_skills(interactions, code)

        return {
            "success": True,
            "codeQuality": code_quality,
            "patterns": patterns,
            "codeIntegration": code_integration,
            "behaviorScore": behavior_score,
            "skills": skills,
            "confidence": 75,
            "explanation": "Code analysis completed",
            "analysisExplanation": _build_explanation(interactions, behavior_score),
        }

    except Exception as e:
        logger.error(f"Error executing analysis: {e}")
        return {"success": False, "explanation": f"Error: {str(e)}"}


# ── scoring helpers ───────────────────────────────────────────────────────────

def _calculate_behavior_score(interactions: List[Dict]) -> int:
    """
    Calculate behavior score 0-100.

    Signals (all event types from Prisma, camelCase):
      prompt_sent       — candidate sent a prompt to AI
      response_received — AI responded
      copy              — candidate copied AI response
      apply             — candidate applied AI suggestion to code
      code_modified     — candidate manually edited code

    Scoring philosophy:
      - Many prompts + few modifications = heavy AI reliance → lower score
      - Apply events show some deliberate use → neutral/positive
      - Manual modifications show independence → positive
      - No AI usage at all → score based on code quality only (70 default)
    """
    if not interactions:
        return 50  # no data, neutral

    prompts       = [i for i in interactions if _evt(i) == "prompt_sent"]
    responses     = [i for i in interactions if _evt(i) == "response_received"]
    copies        = [i for i in interactions if _evt(i) in ("copy", "code_copied_from_ai", "code_copied")]
    applies       = [i for i in interactions if _evt(i) in ("apply", "code_applied", "code_applied_from_ai")]
    modifications = [i for i in interactions if _evt(i) == "code_modified"]

    n_prompts = len(prompts)
    n_copies  = len(copies)
    n_applies = len(applies)
    n_mods    = len(modifications)

    logger.info(
        f"Agent 7 score inputs — prompts:{n_prompts} copies:{n_copies} "
        f"applies:{n_applies} modifications:{n_mods}"
    )

    # No AI usage at all
    if n_prompts == 0:
        return 70  # no AI used; assume independent work, moderate score

    # --- Modification ratio: how much did candidate edit vs just prompt? ---
    # applies + mods = total "deliberate acceptance or editing"
    deliberate = n_applies + n_mods
    mod_ratio  = deliberate / n_prompts  # >1 = edited more than prompted

    # --- Copy-without-edit ratio: raw paste without applying ---
    copy_ratio = n_copies / n_prompts  # high = lots of blind copy-paste

    # Base score from modification ratio (0–80 range)
    if mod_ratio >= 3.0:
        base = 80
    elif mod_ratio >= 2.0:
        base = 70
    elif mod_ratio >= 1.0:
        base = 55
    elif mod_ratio >= 0.5:
        base = 40
    else:
        base = 25  # very few modifications relative to prompts

    # Penalise blind copy-paste
    copy_penalty = min(20, int(copy_ratio * 10))

    # Bonus for manual modifications (shows candidate edited AI output)
    mod_bonus = min(20, n_mods * 2)

    score = max(0, min(100, base - copy_penalty + mod_bonus))

    logger.info(
        f"Agent 7 score: base={base} copy_penalty={copy_penalty} "
        f"mod_bonus={mod_bonus} final={score}"
    )
    return score


def _build_explanation(interactions: List[Dict], score: int) -> str:
    """Build a human-readable explanation of the behavior score."""
    prompts   = [i for i in interactions if _evt(i) == "prompt_sent"]
    copies    = [i for i in interactions if _evt(i) in ("copy", "code_copied_from_ai", "code_copied")]
    applies   = [i for i in interactions if _evt(i) in ("apply", "code_applied", "code_applied_from_ai")]
    mods      = [i for i in interactions if _evt(i) == "code_modified"]

    n_p, n_c, n_a, n_m = len(prompts), len(copies), len(applies), len(mods)

    if n_p == 0:
        return "Candidate did not use the AI assistant during this session."

    parts = [f"Candidate sent {n_p} prompt{'s' if n_p != 1 else ''} to the AI."]

    if n_c > 0:
        parts.append(f"Modified {n_c == 0 and '0' or n_c}% of AI-generated code" +
                     (" and made few critical-review prompts." if n_c > n_p // 2 else "."))
    if n_a > 0:
        parts.append(f"Applied {n_a} AI suggestion{'s' if n_a != 1 else ''} directly.")
    if n_m > 0:
        parts.append(f"Made {n_m} manual code modification{'s' if n_m != 1 else ''}.")

    if score >= 70:
        parts.append("Self-Reliance score indicates good independent coding behaviour.")
    elif score >= 40:
        parts.append("Self-Reliance score suggests moderate dependence on AI assistance.")
    else:
        parts.append("Self-Reliance score suggests heavy reliance on AI for full solutions.")

    return " ".join(parts)


# ── pattern extraction ────────────────────────────────────────────────────────

def _extract_patterns(interactions: List[Dict]) -> Dict[str, Any]:
    """Extract interaction patterns."""
    patterns: Dict[str, Any] = {
        "copyPastePatterns": [],
        "timingPatterns": {},
        "promptPatterns": {}
    }

    copy_events  = [i for i in interactions if _evt(i) in ("copy", "code_copied_from_ai", "code_copied")]
    apply_events = [i for i in interactions if _evt(i) in ("apply", "code_applied", "code_applied_from_ai")]

    for copy_event in copy_events:
        paste = next((p for p in apply_events if _events_close_in_time(copy_event, p)), None)
        if paste:
            patterns["copyPastePatterns"].append({
                "copyTimestamp":  _ts(copy_event) or "",
                "pasteTimestamp": _ts(paste) or "",
                "timeDiff": _time_diff(_ts(copy_event), _ts(paste))
            })

    # Timing gaps between consecutive interactions
    if len(interactions) >= 2:
        gaps = []
        for idx in range(1, len(interactions)):
            gap = _time_diff(_ts(interactions[idx - 1]), _ts(interactions[idx]))
            if gap is not None:
                gaps.append(gap)
        if gaps:
            patterns["timingPatterns"] = {
                "averageGap": sum(gaps) / len(gaps),
                "medianGap":  sorted(gaps)[len(gaps) // 2],
                "totalEvents": len(interactions)
            }

    # Categorise prompts by intent
    prompts = [i for i in interactions if _evt(i) == "prompt_sent"]
    cats = {"solution_request": 0, "explanation_request": 0, "code_review": 0, "other": 0}
    for prompt in prompts:
        text = _prompt_text(prompt).lower()
        if re.search(r"solve|complete|write.*code|implement|generate", text):
            cats["solution_request"] += 1
        elif re.search(r"explain|why|how.*work|what.*does", text):
            cats["explanation_request"] += 1
        elif re.search(r"review|check|improve|fix|debug", text):
            cats["code_review"] += 1
        else:
            cats["other"] += 1
    patterns["promptPatterns"] = cats

    return patterns


def _analyze_code_integration(interactions: List[Dict]) -> Dict[str, Any]:
    """Analyse how AI-generated code was integrated."""
    modifications = [i for i in interactions if _evt(i) == "code_modified"]
    copies        = [i for i in interactions if _evt(i) in ("copy", "code_copied_from_ai", "code_copied")]
    applies       = [i for i in interactions if _evt(i) in ("apply", "code_applied", "code_applied_from_ai")]

    total_ai_use  = len(copies) + len(applies)
    mod_ratio     = len(modifications) / total_ai_use if total_ai_use > 0 else 0

    return {
        "modifications": len(modifications),
        "copies":        len(copies),
        "applies":       len(applies),
        "modificationRatio": round(mod_ratio * 100),  # as percentage
        "integrationQuality": "good" if mod_ratio > 0.5 else "poor"
    }


def _assess_code_quality(code: str) -> Dict[str, Any]:
    """Assess code quality from final snapshot."""
    if not code:
        return {}

    lines          = code.split("\n")
    total_lines    = len(lines)
    non_empty      = len([l for l in lines if l.strip()])
    comments       = len([l for l in lines if l.strip().startswith("#") or l.strip().startswith("//")])
    max_indent     = max((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    complexity     = "low" if max_indent < 8 else "medium" if max_indent < 16 else "high"

    return {
        "totalLines":    total_lines,
        "nonEmptyLines": non_empty,
        "comments":      comments,
        "commentRatio":  round(comments / non_empty, 2) if non_empty > 0 else 0,
        "complexity":    complexity,
        "maxIndentation": max_indent
    }


def _assess_skills(interactions: List[Dict], code: Optional[str]) -> Dict[str, Any]:
    """Assess candidate skills from interactions and code."""
    skills = {"problemSolving": "medium", "codeQuality": "medium", "independence": "medium"}

    prompts       = [i for i in interactions if _evt(i) == "prompt_sent"]
    modifications = [i for i in interactions if _evt(i) == "code_modified"]
    applies       = [i for i in interactions if _evt(i) in ("apply", "code_applied", "code_applied_from_ai")]

    if prompts:
        independence_ratio = (len(modifications) + len(applies)) / len(prompts)
        if independence_ratio > 2:
            skills["independence"] = "high"
        elif independence_ratio < 0.5:
            skills["independence"] = "low"

    if code:
        lines = code.split("\n")
        if len(lines) > 50:
            skills["codeQuality"] = "high"
        elif len(lines) < 10:
            skills["codeQuality"] = "low"

    return skills


# ── time utilities ────────────────────────────────────────────────────────────

def _events_close_in_time(event1: Dict, event2: Dict, threshold_seconds: int = 30) -> bool:
    diff = _time_diff(_ts(event1), _ts(event2))
    return diff is not None and 0 < diff < threshold_seconds


def _time_diff(timestamp1: Any, timestamp2: Any) -> Optional[float]:
    try:
        from dateutil.parser import parse
        if isinstance(timestamp1, str):
            timestamp1 = parse(timestamp1)
        if isinstance(timestamp2, str):
            timestamp2 = parse(timestamp2)
        if isinstance(timestamp1, datetime) and isinstance(timestamp2, datetime):
            diff = (timestamp2 - timestamp1).total_seconds()
            return diff if diff > 0 else None
    except Exception:
        pass
    return None
