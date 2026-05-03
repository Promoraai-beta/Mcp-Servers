"""
Bug Narrative Builder
Creates a story of how each injected bug was handled by the candidate.

For each bug, reconstructs:
1. Was it discovered? When?
2. Did the candidate ask AI about it?
3. Did they fix it? How?
4. Did they verify the fix?
5. What was the overall quality of their approach?

This replaces "was_fixed: True/False" with a rich, explainable narrative.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def build_bug_narratives(
    injected_bug_ids: List[str],
    expected_signals: Dict[str, Any],
    diff_evidence: Dict[str, Dict],
    sequence_chains: List[Dict],
    terminal_analysis: Dict,
    interactions: List[Dict],
    final_files: Dict[str, str],
) -> Dict[str, Dict[str, Any]]:
    """
    Build a detailed narrative for each injected bug.

    Returns: {bug_id: {narrative, score, timeline, evidence_quality}}
    """
    narratives = {}

    for bug_id in injected_bug_ids:
        signal = expected_signals.get(bug_id, {})
        description = signal.get("description", bug_id)

        narrative = _build_single_narrative(
            bug_id, description,
            diff_evidence.get(bug_id, {}),
            sequence_chains,
            terminal_analysis,
            interactions,
            final_files,
        )
        narratives[bug_id] = narrative

    return narratives


def _build_single_narrative(
    bug_id: str,
    description: str,
    diff_ev: Dict,
    chains: List[Dict],
    terminal: Dict,
    interactions: List[Dict],
    final_files: Dict[str, str],
) -> Dict[str, Any]:
    """Build narrative for a single bug."""

    # 1. Discovery: did they mention it in prompts?
    discovery = _check_discovery(bug_id, description, interactions)

    # 2. AI assistance: did they ask AI to help fix it?
    ai_help = _check_ai_assistance(bug_id, description, chains)

    # 3. Fix from diffs
    fix_evidence = diff_ev
    fix_quality = fix_evidence.get("fixQuality", "not_addressed")

    # 4. Final code check (was it actually fixed in the final state?)
    final_fixed = _check_final_state(bug_id, final_files)

    # 5. Verification: did they test after addressing this bug?
    verified = _check_verification(bug_id, diff_ev, terminal, interactions)

    # Build timeline
    timeline = _build_bug_timeline(bug_id, discovery, ai_help, fix_evidence, verified)

    # Score this bug handling (0-10)
    score = _score_bug_handling(
        discovered=discovery["discovered"],
        used_ai=ai_help["usedAI"],
        fix_quality=fix_quality,
        final_fixed=final_fixed,
        verified=verified["verified"],
        ai_dependency=ai_help.get("blindlyFollowed", False),
    )

    # Generate human-readable narrative
    text = _generate_narrative_text(
        bug_id, description, discovery, ai_help,
        fix_quality, final_fixed, verified, score,
    )

    return {
        "bugId": bug_id,
        "description": description,
        "score": score,
        "discovery": discovery,
        "aiAssistance": ai_help,
        "fixQuality": fix_quality,
        "finalFixed": final_fixed,
        "verification": verified,
        "timeline": timeline,
        "narrativeText": text,
    }


# ─── Discovery ─────────────────────────────────────────────────────────────────

def _check_discovery(
    bug_id: str, description: str, interactions: List[Dict]
) -> Dict[str, Any]:
    """Did the candidate acknowledge/discover this bug?"""
    keywords = _bug_keywords(bug_id, description)

    # Check prompts
    prompts = [
        e for e in interactions
        if e.get("event_type") == "prompt_sent"
    ]

    first_mention = None
    mentions = 0

    for p in prompts:
        text = (p.get("prompt_text", "") or "").lower()
        if any(kw in text for kw in keywords):
            mentions += 1
            if first_mention is None:
                first_mention = p.get("timestamp")

    return {
        "discovered": mentions > 0,
        "firstMentionedAt": first_mention,
        "mentionCount": mentions,
    }


# ─── AI assistance ─────────────────────────────────────────────────────────────

def _check_ai_assistance(
    bug_id: str, description: str, chains: List[Dict]
) -> Dict[str, Any]:
    """
    Did the candidate ask AI specifically about this bug?
    If so, did they blindly follow the response or adapt it?
    """
    keywords = _bug_keywords(bug_id, description)

    relevant_chains = []
    for chain in chains:
        prompt = (chain.get("promptText", "") or "").lower()
        if any(kw in prompt for kw in keywords):
            relevant_chains.append(chain)

    if not relevant_chains:
        return {"usedAI": False, "chainTypes": [], "blindlyFollowed": False}

    chain_types = [c.get("chainType", "unknown") for c in relevant_chains]
    prompt_categories = [c.get("promptCategory", "broad") for c in relevant_chains]

    # Did they blindly paste the AI response without modification?
    blindly_followed = "blind_paste" in chain_types and len(chain_types) == 1

    return {
        "usedAI": True,
        "chainTypes": chain_types,
        "promptCategories": prompt_categories,
        "blindlyFollowed": blindly_followed,
        "adapted": any(ct in ("adapted", "verified") for ct in chain_types),
    }


# ─── Final state check ────────────────────────────────────────────────────────

def _check_final_state(bug_id: str, final_files: Dict[str, str]) -> bool:
    """Check if the bug is actually fixed in the final code."""
    if not final_files:
        return False

    all_code = "\n".join(v for v in final_files.values() if isinstance(v, str))
    code_lower = all_code.lower()

    # Reuse the existing fix_checks logic but with cleaner patterns
    fix_checks = {
        "bug_key_prop": lambda c: "key={" in c,
        "bug_input_not_cleared": lambda c: "setinput('')" in c or 'setinput("")' in c,
        "bug_no_focus_styles": lambda c: ":focus" in c or "focus-visible" in c or "outline" in c,
        "bug_useeffect_deps": lambda c: bool(re.search(r"useeffect\([^)]*\[[^\]]+\]", c)),
        "bug_stale_closure": lambda c: "usecallback" in c or "useref" in c,
        "bug_misleading_comment": lambda c: "ai-generated: this component handles all task management correctly" not in c,
        "bug_no_error_handling": lambda c: ".catch(" in c or "response.ok" in c or "res.ok" in c,
        "bug_sql_injection": lambda c: ("?" in c and ("prepare" in c or "placeholder" in c)),
        "bug_missing_validation": lambda c: "trim" in c or "!title" in c or "required" in c,
        "bug_no_404": lambda c: "404" in c and "notfound" in c.replace(" ", "").replace("_", ""),
        "bug_auth_missing": lambda c: "authenticate" in c and ("middleware" in c or "require" in c),
        "bug_error_handler_200": lambda c: bool(re.search(r"status\s*\(\s*500", c)),
        "bug_spec_mismatch": lambda c: "archived" in c and ("filter" in c or "where" in c),
        "bug_auth_not_wired": lambda c: "authenticate" in c and ("router" in c or "app.use" in c),
        "bug_post_returns_200": lambda c: bool(re.search(r"status\s*\(\s*201", c)),
        "bug_no_rate_limit": lambda c: "ratelimit" in c.replace("-", "").replace("_", "").replace(" ", ""),
        "bug_unnecessary_rerenders": lambda c: "memo" in c or "usememo" in c or "usecallback" in c,
    }

    checker = fix_checks.get(bug_id)
    if checker:
        try:
            return checker(code_lower)
        except Exception:
            return False
    return False


# ─── Verification ──────────────────────────────────────────────────────────────

def _check_verification(
    bug_id: str,
    diff_ev: Dict,
    terminal: Dict,
    interactions: List[Dict],
) -> Dict[str, Any]:
    """
    Did the candidate verify their fix by running tests or checking output?
    """
    if not diff_ev.get("addressed"):
        return {"verified": False, "method": "not_applicable"}

    # When was the last diff related to this bug?
    relevant_diffs = diff_ev.get("relevantDiffs", [])
    if not relevant_diffs:
        return {"verified": False, "method": "no_diff_data"}

    last_diff_ts = relevant_diffs[-1].get("timestamp", "")

    # Check if any test was run AFTER the last related diff
    test_behavior = terminal.get("testBehavior", {})
    test_timeline = test_behavior.get("testRunTimeline", [])

    for test_run in test_timeline:
        test_ts = test_run.get("timestamp", "")
        if test_ts and last_diff_ts and test_ts > last_diff_ts:
            return {"verified": True, "method": "test_run_after_fix"}

    # Check if they ran dev server (visual verification)
    if terminal.get("devServer", {}).get("started"):
        return {"verified": True, "method": "visual_check_possible"}

    return {"verified": False, "method": "no_verification_detected"}


# ─── Scoring ───────────────────────────────────────────────────────────────────

def _score_bug_handling(
    discovered: bool,
    used_ai: bool,
    fix_quality: str,
    final_fixed: bool,
    verified: bool,
    ai_dependency: bool,
) -> float:
    """
    Score how well the candidate handled this bug (0-10).

    Scoring philosophy:
    - Discovery alone is worth something (awareness)
    - Correct fix is worth a lot
    - Verification adds value
    - Using AI is fine if you adapted/verified
    - Blindly following AI penalizes
    """
    score = 0.0

    # Discovery (0-2)
    if discovered:
        score += 2.0

    # Fix quality (0-5)
    fix_scores = {
        "correct_fix": 5.0,
        "partial_fix": 3.0,
        "wrong_fix": 1.0,
        "attempted": 1.5,
        "not_addressed": 0.0,
    }
    score += fix_scores.get(fix_quality, 0.0)

    # Final state confirmation (0-1)
    if final_fixed:
        score += 1.0

    # Verification (0-1.5)
    if verified:
        score += 1.5

    # AI usage modifier (-1 to +0.5)
    if used_ai and ai_dependency:
        score -= 1.0  # blindly followed AI
    elif used_ai and not ai_dependency:
        score += 0.5  # used AI wisely (asked then adapted)

    return round(max(0, min(10, score)), 1)


# ─── Narrative text ────────────────────────────────────────────────────────────

def _generate_narrative_text(
    bug_id: str,
    description: str,
    discovery: Dict,
    ai_help: Dict,
    fix_quality: str,
    final_fixed: bool,
    verification: Dict,
    score: float,
) -> str:
    """Generate a human-readable narrative for this bug."""
    parts = []

    # Discovery
    if discovery["discovered"]:
        parts.append(f"Candidate identified this issue (mentioned {discovery['mentionCount']} time(s) in prompts).")
    else:
        parts.append("Candidate did not explicitly mention or acknowledge this issue.")

    # AI usage
    if ai_help["usedAI"]:
        if ai_help.get("blindlyFollowed"):
            parts.append("Asked AI for help and applied the suggestion without modification.")
        elif ai_help.get("adapted"):
            parts.append("Asked AI for help, then adapted the response before applying.")
        else:
            parts.append("Referenced AI assistance for this issue.")
    else:
        if fix_quality not in ("not_addressed",):
            parts.append("Fixed without asking AI for help — worked independently.")

    # Fix quality
    fix_text = {
        "correct_fix": "Applied a correct and complete fix.",
        "partial_fix": "Applied a partial fix — some aspects still need attention.",
        "wrong_fix": "Attempted a fix but it introduces new issues.",
        "attempted": "Made changes in the related area but fix is unclear.",
        "not_addressed": "Did not address this issue.",
    }
    parts.append(fix_text.get(fix_quality, "Fix status unknown."))

    # Final state
    if final_fixed:
        parts.append("Bug appears resolved in the final code.")
    elif fix_quality != "not_addressed":
        parts.append("Bug may still be present in the final code.")

    # Verification
    if verification["verified"]:
        method = verification.get("method", "unknown")
        if method == "test_run_after_fix":
            parts.append("Verified the fix by running tests.")
        elif method == "visual_check_possible":
            parts.append("Had dev server running for visual verification.")
    elif fix_quality not in ("not_addressed",):
        parts.append("No verification step detected after the fix.")

    return " ".join(parts)


# ─── Bug timeline ─────────────────────────────────────────────────────────────

def _build_bug_timeline(
    bug_id: str,
    discovery: Dict,
    ai_help: Dict,
    fix_evidence: Dict,
    verification: Dict,
) -> List[Dict[str, Any]]:
    """Build a chronological timeline of events related to this bug."""
    events = []

    if discovery["discovered"] and discovery.get("firstMentionedAt"):
        events.append({
            "timestamp": discovery["firstMentionedAt"],
            "event": "discovered",
            "detail": "First mentioned in prompt",
        })

    for diff in fix_evidence.get("relevantDiffs", []):
        events.append({
            "timestamp": diff.get("timestamp"),
            "event": "fix_attempted",
            "detail": f"Code change ({diff.get('fixType', 'unknown')})",
        })

    # Sort by timestamp
    events.sort(key=lambda e: e.get("timestamp") or "")
    return events


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _bug_keywords(bug_id: str, description: str) -> List[str]:
    """Extract search keywords from a bug."""
    keyword_map = {
        "bug_key_prop": ["key", "unique key", "missing key", "list key"],
        "bug_input_not_cleared": ["clear", "reset", "setinput", "input field"],
        "bug_no_focus_styles": ["focus", "outline", "keyboard", "accessibility", "a11y"],
        "bug_useeffect_deps": ["dependency", "useeffect", "deps", "infinite loop"],
        "bug_stale_closure": ["stale", "closure", "stale closure"],
        "bug_misleading_comment": ["misleading", "comment", "incorrect comment"],
        "bug_no_error_handling": ["error handling", "catch", "try catch", "fetch error"],
        "bug_sql_injection": ["sql injection", "parameterized", "prepared statement", "sanitize"],
        "bug_missing_validation": ["validation", "required", "empty", "input validation"],
        "bug_no_404": ["404", "not found", "missing resource"],
        "bug_auth_missing": ["auth", "authentication", "unauthorized", "middleware"],
        "bug_error_handler_200": ["error handler", "status code", "500", "error response"],
        "bug_spec_mismatch": ["openapi", "spec", "mismatch", "archived"],
        "bug_auth_not_wired": ["middleware", "auth middleware", "route protection"],
        "bug_post_returns_200": ["201", "created", "post response"],
        "bug_no_rate_limit": ["rate limit", "throttle", "abuse", "dos"],
        "bug_unnecessary_rerenders": ["memo", "rerender", "performance", "usememo"],
    }

    keywords = keyword_map.get(bug_id, [])
    desc_words = [w.lower() for w in description.split() if len(w) > 3]
    return list(set(keywords + desc_words[:5]))
