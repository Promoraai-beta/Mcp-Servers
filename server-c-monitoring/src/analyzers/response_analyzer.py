"""
Response Analyzer
Analyzes the AI responses the candidate received and what they did with them.

Key insight: the frontend sends responseText for each AI response.
We can check: did the AI give the answer? Did the candidate apply it verbatim?
"""

import re
import logging
from difflib import SequenceMatcher
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


# ── field helpers (Prisma returns camelCase; IDE may send snake_case) ─────────

def _evt(e: Dict) -> str:
    """Return event type regardless of camelCase vs snake_case."""
    return e.get("eventType") or e.get("event_type") or ""

def _prompt_text(e: Dict) -> str:
    return e.get("promptText") or e.get("prompt_text") or ""

def _response_text(e: Dict) -> str:
    return e.get("responseText") or e.get("response_text") or ""

def _code_snippet(e: Dict) -> str:
    return e.get("codeSnippet") or e.get("code_snippet") or ""

def _ts(e: Dict):
    return e.get("timestamp") or e.get("created_at")


def analyze_responses(interactions: List[Dict]) -> Dict[str, Any]:
    """
    Analyze AI responses and how the candidate used them.

    Returns:
        - response_quality: were responses code-heavy or explanation-heavy?
        - adoption_patterns: how much of AI responses ended up in code?
        - verbatim_detection: were responses copied without changes?
        - ai_as_teacher_vs_coder: did the candidate use AI to learn or to write code?
    """
    prompt_response_pairs = _pair_prompts_responses(interactions)

    if not prompt_response_pairs:
        return _empty_result()

    response_quality = _analyze_response_types(prompt_response_pairs)
    adoption = _analyze_adoption(prompt_response_pairs, interactions)
    usage_pattern = _classify_ai_usage(prompt_response_pairs)

    return {
        "totalPairs": len(prompt_response_pairs),
        "responseQuality": response_quality,
        "adoptionPatterns": adoption,
        "usagePattern": usage_pattern,
    }


# ─── Pair prompts with responses ──────────────────────────────────────────────

def _pair_prompts_responses(interactions: List[Dict]) -> List[Dict[str, Any]]:
    """Pair each prompt_sent with its response_received."""
    pairs = []
    sorted_events = sorted(interactions, key=lambda e: _ts(e) or "")

    i = 0
    while i < len(sorted_events):
        event = sorted_events[i]
        if _evt(event) == "prompt_sent":
            prompt_text = _prompt_text(event)
            response_text = ""
            response_ts = None

            # Find the next response_received
            for j in range(i + 1, min(i + 10, len(sorted_events))):
                if _evt(sorted_events[j]) == "response_received":
                    response_text = _response_text(sorted_events[j]) or ""
                    response_ts = _ts(sorted_events[j])
                    break

            pairs.append({
                "promptText": prompt_text,
                "responseText": response_text,
                "promptTimestamp": _ts(event),
                "responseTimestamp": response_ts,
            })
        i += 1

    return pairs


# ─── Response type analysis ───────────────────────────────────────────────────

def _analyze_response_types(pairs: List[Dict]) -> Dict[str, Any]:
    """Categorize what the AI responses contained."""
    code_heavy = 0
    explanation_heavy = 0
    mixed = 0
    empty_or_short = 0

    for pair in pairs:
        resp = pair.get("responseText", "")
        if len(resp) < 20:
            empty_or_short += 1
            continue

        code_blocks = len(re.findall(r"```", resp))
        has_code = code_blocks >= 2  # at least one code block (open + close)

        # Count non-code text
        text_without_code = re.sub(r"```[\s\S]*?```", "", resp)
        has_explanation = len(text_without_code.strip()) > 100

        if has_code and has_explanation:
            mixed += 1
        elif has_code:
            code_heavy += 1
        elif has_explanation:
            explanation_heavy += 1
        else:
            empty_or_short += 1

    total = len(pairs) or 1
    return {
        "codeHeavy": code_heavy,
        "explanationHeavy": explanation_heavy,
        "mixed": mixed,
        "emptyOrShort": empty_or_short,
        "codeHeavyRatio": round(code_heavy / total, 2),
    }


# ─── Adoption analysis ────────────────────────────────────────────────────────

def _analyze_adoption(
    pairs: List[Dict],
    interactions: List[Dict],
) -> Dict[str, Any]:
    """
    Check: how much of AI response code actually ended up in the codebase?
    Uses code_pasted_from_ai events and compares snippets to responses.
    """
    paste_events = [
        e for e in interactions
        if _evt(e) in ("code_pasted_from_ai", "code_copied_from_ai", "code_applied")
    ]

    verbatim_count = 0
    adapted_count = 0
    total_checked = 0

    for paste in paste_events:
        meta = _parse_metadata(paste.get("metadata"))
        snippet = _code_snippet(paste) or meta.get("codeSnippet", "")
        if not snippet or len(snippet) < 20:
            continue

        # Find the most recent response before this paste
        paste_ts = _ts(paste) or ""
        closest_response = None
        for pair in reversed(pairs):
            resp_ts = pair.get("responseTimestamp", "") or ""
            if resp_ts and resp_ts <= paste_ts:
                closest_response = pair.get("responseText", "")
                break

        if not closest_response:
            continue

        total_checked += 1

        # Extract code blocks from response
        code_blocks = re.findall(r"```\w*\n([\s\S]*?)```", closest_response)
        response_code = "\n".join(code_blocks)

        if not response_code:
            response_code = closest_response

        # Compare snippet to response code
        similarity = _compute_similarity(snippet.strip(), response_code.strip())

        if similarity > 0.85:
            verbatim_count += 1
        elif similarity > 0.4:
            adapted_count += 1

    total = max(total_checked, 1)
    return {
        "totalPastesChecked": total_checked,
        "verbatimPastes": verbatim_count,
        "adaptedPastes": adapted_count,
        "verbatimRate": round(verbatim_count / total, 2),
        "adaptedRate": round(adapted_count / total, 2),
    }


# ─── AI usage classification ──────────────────────────────────────────────────

def _classify_ai_usage(pairs: List[Dict]) -> Dict[str, Any]:
    """
    Overall classification of how the candidate used AI:
    - "teacher": mostly asked explanations
    - "coder": mostly asked for implementations
    - "debugger": mostly asked about errors
    - "balanced": mix of approaches
    """
    categories = {"explanation": 0, "solution": 0, "debugging": 0, "other": 0}

    for pair in pairs:
        prompt = (pair.get("promptText", "") or "").lower()
        if re.search(r"explain|how|why|what does|understand", prompt):
            categories["explanation"] += 1
        elif re.search(r"fix|debug|error|bug|failing|broken", prompt):
            categories["debugging"] += 1
        elif re.search(r"write|implement|create|build|solve|complete", prompt):
            categories["solution"] += 1
        else:
            categories["other"] += 1

    total = sum(categories.values()) or 1
    dominant = max(categories, key=categories.get)

    if categories[dominant] / total > 0.5:
        pattern = {
            "explanation": "ai_as_teacher",
            "solution": "ai_as_coder",
            "debugging": "ai_as_debugger",
            "other": "ai_as_general",
        }.get(dominant, "balanced")
    else:
        pattern = "balanced"

    return {
        "pattern": pattern,
        "breakdown": categories,
        "dominantCategory": dominant,
        "dominantRatio": round(categories[dominant] / total, 2),
    }


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _compute_similarity(text1: str, text2: str) -> float:
    """Compute text similarity using SequenceMatcher."""
    if not text1 or not text2:
        return 0.0
    # For very long texts, sample
    if len(text1) > 2000:
        text1 = text1[:2000]
    if len(text2) > 2000:
        text2 = text2[:2000]
    return SequenceMatcher(None, text1, text2).ratio()


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


def _empty_result() -> Dict[str, Any]:
    return {
        "totalPairs": 0,
        "responseQuality": {},
        "adoptionPatterns": {"verbatimRate": 0, "adaptedRate": 0},
        "usagePattern": {"pattern": "no_data"},
    }
