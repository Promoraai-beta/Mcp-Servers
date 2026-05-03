"""
Diff Analyzer
Compares codeBefore / codeAfter from real events to detect *actual changes*.
This replaces keyword-matching with real diff-based detection.

Key insight: The frontend useAIWatcher hook sends codeBefore and codeAfter
with each code_modified and code_pasted_from_ai event. We use those to
build a real picture of what changed per file.
"""

import re
import logging
from difflib import unified_diff, SequenceMatcher
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def analyze_diffs(
    interactions: List[Dict],
    injected_bug_ids: List[str],
    expected_signals: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze codeBefore/codeAfter diffs across all interactions.

    Returns:
        - per-bug diff evidence (was the bugged pattern removed/replaced?)
        - overall change map (which files changed, how much)
        - code origin tracking (AI-pasted vs self-written)
    """
    # Collect all diffs from events that have codeBefore/codeAfter
    diff_events = _extract_diff_events(interactions)

    # Track file-level changes
    file_change_map = _build_file_change_map(diff_events)

    # Track code origin: pasted from AI vs self-written
    code_origins = _track_code_origins(interactions)

    # Per-bug evidence from diffs
    bug_evidence = _evaluate_bugs_from_diffs(
        diff_events, injected_bug_ids, expected_signals
    )

    return {
        "totalDiffEvents": len(diff_events),
        "fileChangeMap": file_change_map,
        "codeOrigins": code_origins,
        "bugEvidence": bug_evidence,
    }


# ─── Diff event extraction ────────────────────────────────────────────────────

def _extract_diff_events(interactions: List[Dict]) -> List[Dict[str, Any]]:
    """Pull out events that have codeBefore/codeAfter."""
    diff_events = []

    for event in interactions:
        meta = _parse_metadata(event.get("metadata"))
        code_before = event.get("code_before") or meta.get("codeBefore", "")
        code_after = event.get("code_after") or meta.get("codeAfter", "")
        code_snippet = event.get("code_snippet") or meta.get("codeSnippet", "")

        if not code_before and not code_after and not code_snippet:
            continue

        diff_events.append({
            "eventType": event.get("event_type", ""),
            "timestamp": event.get("timestamp", ""),
            "codeBefore": code_before or "",
            "codeAfter": code_after or "",
            "codeSnippet": code_snippet or "",
            "modificationDepth": meta.get("modificationDepth", 0),
            "timeSinceCopy": meta.get("timeSinceCopy"),
            "filePath": meta.get("filePath", "unknown"),
        })

    return diff_events


def _build_file_change_map(diff_events: List[Dict]) -> Dict[str, Any]:
    """Track changes per file: how many edits, total lines changed."""
    file_map: Dict[str, Dict] = {}

    for event in diff_events:
        fp = event.get("filePath", "unknown")
        if fp not in file_map:
            file_map[fp] = {
                "editCount": 0,
                "linesAdded": 0,
                "linesRemoved": 0,
                "aiPasteCount": 0,
                "selfEditCount": 0,
            }

        file_map[fp]["editCount"] += 1

        before = event.get("codeBefore", "")
        after = event.get("codeAfter", "")
        if before or after:
            added, removed = _count_diff_lines(before, after)
            file_map[fp]["linesAdded"] += added
            file_map[fp]["linesRemoved"] += removed

        if event.get("eventType") in ("code_pasted_from_ai", "code_copied_from_ai"):
            file_map[fp]["aiPasteCount"] += 1
        else:
            file_map[fp]["selfEditCount"] += 1

    return file_map


def _track_code_origins(interactions: List[Dict]) -> Dict[str, Any]:
    """Track how much code came from AI vs was self-written."""
    ai_paste_chars = 0
    self_written_chars = 0
    total_modifications = 0

    for event in interactions:
        etype = event.get("event_type", "")
        meta = _parse_metadata(event.get("metadata"))

        if etype in ("code_pasted_from_ai", "code_copied_from_ai"):
            snippet = event.get("code_snippet") or meta.get("codeSnippet", "")
            ai_paste_chars += len(snippet)
        elif etype == "code_modified":
            code_after = event.get("code_after") or meta.get("codeAfter", "")
            code_before = event.get("code_before") or meta.get("codeBefore", "")
            # Net new chars from self-edit
            if code_after and code_before:
                self_written_chars += max(0, len(code_after) - len(code_before))
            total_modifications += 1

    total = ai_paste_chars + self_written_chars
    ai_ratio = ai_paste_chars / total if total > 0 else 0

    return {
        "aiPastedChars": ai_paste_chars,
        "selfWrittenChars": self_written_chars,
        "aiCodeRatio": round(ai_ratio, 2),
        "totalModifications": total_modifications,
        "assessment": (
            "mostly_ai" if ai_ratio > 0.7
            else "balanced" if ai_ratio > 0.3
            else "mostly_self"
        ),
    }


# ─── Per-bug diff evidence ────────────────────────────────────────────────────

def _evaluate_bugs_from_diffs(
    diff_events: List[Dict],
    injected_bug_ids: List[str],
    expected_signals: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    For each bug, check if the *diffs* show the bug was addressed.
    This is more reliable than just checking the final code.
    """
    evidence = {}

    for bug_id in injected_bug_ids:
        signal = expected_signals.get(bug_id, {})
        description = signal.get("description", "")
        patterns = _get_bug_diff_patterns(bug_id)

        bug_evidence = {
            "addressed": False,
            "diffMentions": 0,
            "relevantDiffs": [],
            "fixQuality": "not_addressed",
        }

        for event in diff_events:
            before = event.get("codeBefore", "")
            after = event.get("codeAfter", "")
            snippet = event.get("codeSnippet", "")

            if not before and not after and not snippet:
                continue

            # Check if this diff is related to the bug
            relevance = _check_diff_relevance(bug_id, patterns, before, after, snippet)
            if relevance["relevant"]:
                bug_evidence["diffMentions"] += 1
                bug_evidence["relevantDiffs"].append({
                    "timestamp": event.get("timestamp"),
                    "eventType": event.get("eventType"),
                    "fixType": relevance["fixType"],
                    "filePath": event.get("filePath"),
                })

        if bug_evidence["diffMentions"] > 0:
            bug_evidence["addressed"] = True
            # Determine fix quality from the best diff
            fix_types = [d["fixType"] for d in bug_evidence["relevantDiffs"]]
            if "correct_fix" in fix_types:
                bug_evidence["fixQuality"] = "correct_fix"
            elif "partial_fix" in fix_types:
                bug_evidence["fixQuality"] = "partial_fix"
            elif "wrong_fix" in fix_types:
                bug_evidence["fixQuality"] = "wrong_fix"
            else:
                bug_evidence["fixQuality"] = "attempted"

        # Cap relevantDiffs for payload size
        bug_evidence["relevantDiffs"] = bug_evidence["relevantDiffs"][:5]
        evidence[bug_id] = bug_evidence

    return evidence


def _get_bug_diff_patterns(bug_id: str) -> Dict[str, Any]:
    """
    For each known bug type, define what the *bad* code looks like and what
    the *fix* code looks like — so we can match against diffs.
    """
    patterns = {
        "bug_key_prop": {
            "bad_patterns": [r"\.map\(\s*\(\s*\w+\s*\)\s*=>\s*<\w+\s+(?!key)"],  # .map without key
            "fix_patterns": [r"key=\{", r"key=\{.*?\.id\}", r"key=\{.*?index\}"],
            "context_keywords": ["key", "map", "list"],
        },
        "bug_input_not_cleared": {
            "bad_patterns": [],
            "fix_patterns": [r"setInput\s*\(\s*['\"][\s]*['\"]\s*\)", r"\.value\s*=\s*['\"][\s]*['\"]"],
            "context_keywords": ["setinput", "clear", "reset", "input", "value"],
        },
        "bug_no_focus_styles": {
            "bad_patterns": [],
            "fix_patterns": [r":focus\s*\{", r"outline[:\s]", r"focus-visible", r"focus-within"],
            "context_keywords": ["focus", "outline", "accessibility", "keyboard"],
        },
        "bug_useeffect_deps": {
            "bad_patterns": [r"useEffect\([^)]*\[\s*\]"],  # empty deps array when should have deps
            "fix_patterns": [r"useEffect\([^)]*\[[^\]]+\]"],  # non-empty deps array
            "context_keywords": ["useeffect", "dependency", "deps"],
        },
        "bug_stale_closure": {
            "bad_patterns": [],
            "fix_patterns": [r"useEffect\([^)]*\[.*?key", r"useCallback", r"useRef"],
            "context_keywords": ["closure", "stale", "key", "ref"],
        },
        "bug_misleading_comment": {
            "bad_patterns": [r"ai-generated.*correctly"],
            "fix_patterns": [],  # removing the comment is the fix
            "context_keywords": ["ai-generated", "comment", "misleading"],
        },
        "bug_no_error_handling": {
            "bad_patterns": [],
            "fix_patterns": [r"\.catch\(", r"response\.ok", r"res\.ok", r"try\s*\{", r"if\s*\(!.*ok\)"],
            "context_keywords": ["catch", "error", "try", "ok"],
        },
        "bug_sql_injection": {
            "bad_patterns": [r"\$\{.*?\}", r"'\s*\+\s*\w+"],  # string concatenation in SQL
            "fix_patterns": [r"\?\s*,", r"prepare", r"parameterized", r"placeholder"],
            "context_keywords": ["sql", "injection", "parameterized", "prepare"],
        },
        "bug_missing_validation": {
            "bad_patterns": [],
            "fix_patterns": [r"!title|title\.trim|required|validate|if\s*\(\s*!"],
            "context_keywords": ["validation", "required", "trim", "empty"],
        },
        "bug_no_404": {
            "bad_patterns": [],
            "fix_patterns": [r"404", r"not.*found", r"res\.status\s*\(\s*404"],
            "context_keywords": ["404", "not found"],
        },
        "bug_auth_missing": {
            "bad_patterns": [],
            "fix_patterns": [r"authenticate", r"auth.*middleware", r"requireAuth", r"isAuth"],
            "context_keywords": ["auth", "middleware", "token"],
        },
        "bug_error_handler_200": {
            "bad_patterns": [r"res\.status\s*\(\s*200\s*\).*error"],
            "fix_patterns": [r"res\.status\s*\(\s*500\s*\)", r"res\.status\s*\(\s*4\d\d\s*\)"],
            "context_keywords": ["error", "500", "status"],
        },
        "bug_spec_mismatch": {
            "bad_patterns": [],
            "fix_patterns": [r"archived", r"isArchived", r"filter.*archived"],
            "context_keywords": ["spec", "openapi", "mismatch", "archived"],
        },
        "bug_auth_not_wired": {
            "bad_patterns": [],
            "fix_patterns": [r"router\.\w+.*authenticate", r"app\.use.*auth"],
            "context_keywords": ["router", "middleware", "wire"],
        },
        "bug_post_returns_200": {
            "bad_patterns": [r"res\.status\s*\(\s*200\s*\).*creat"],
            "fix_patterns": [r"res\.status\s*\(\s*201\s*\)"],
            "context_keywords": ["201", "created"],
        },
        "bug_no_rate_limit": {
            "bad_patterns": [],
            "fix_patterns": [r"rateLimit", r"rate-limit", r"express-rate-limit", r"throttle"],
            "context_keywords": ["rate", "limit", "throttle"],
        },
        "bug_unnecessary_rerenders": {
            "bad_patterns": [],
            "fix_patterns": [r"React\.memo", r"useMemo", r"useCallback", r"memo\("],
            "context_keywords": ["memo", "performance", "rerender"],
        },
    }
    return patterns.get(bug_id, {"bad_patterns": [], "fix_patterns": [], "context_keywords": []})


def _check_diff_relevance(
    bug_id: str,
    patterns: Dict[str, Any],
    before: str, after: str, snippet: str,
) -> Dict[str, Any]:
    """
    Check if a specific diff event is relevant to a specific bug.
    Returns relevance + fix type.
    """
    # Check context keywords first (are we in the right area?)
    context_kws = patterns.get("context_keywords", [])
    all_text = (before + after + snippet).lower()

    keyword_hits = sum(1 for kw in context_kws if kw in all_text)
    if keyword_hits == 0:
        return {"relevant": False, "fixType": None}

    # Check fix patterns in "after" code (or snippet if "after" is empty)
    fix_text = after or snippet
    fix_patterns = patterns.get("fix_patterns", [])
    bad_patterns = patterns.get("bad_patterns", [])

    fix_matches = sum(1 for p in fix_patterns if re.search(p, fix_text, re.IGNORECASE))
    bad_removed = False

    # Check if bad pattern was in "before" but not in "after"
    for bp in bad_patterns:
        if before and re.search(bp, before, re.IGNORECASE):
            if not after or not re.search(bp, after, re.IGNORECASE):
                bad_removed = True

    if bad_removed and fix_matches > 0:
        return {"relevant": True, "fixType": "correct_fix"}
    if fix_matches > 0:
        return {"relevant": True, "fixType": "partial_fix"}
    if bad_removed:
        return {"relevant": True, "fixType": "partial_fix"}
    if keyword_hits >= 2:
        return {"relevant": True, "fixType": "attempted"}

    return {"relevant": False, "fixType": None}


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _count_diff_lines(before: str, after: str) -> Tuple[int, int]:
    """Count added and removed lines between before and after."""
    before_lines = before.split("\n") if before else []
    after_lines = after.split("\n") if after else []

    diff = list(unified_diff(before_lines, after_lines, lineterm=""))
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    return added, removed


def _parse_metadata(meta: Any) -> Dict:
    if isinstance(meta, dict):
        return meta
    if isinstance(meta, str):
        try:
            import json
            return json.loads(meta)
        except Exception:
            return {}
    return {}
