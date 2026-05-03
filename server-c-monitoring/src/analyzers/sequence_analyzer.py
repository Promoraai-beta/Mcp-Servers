"""
Sequence Analyzer
Understands the *order* of events — not just counts.

Core concept: Prompt → Response → Action chains.
What did the candidate do AFTER each AI interaction? That's the fluency signal.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def analyze_sequences(interactions: List[Dict]) -> Dict[str, Any]:
    """
    Analyze the full event sequence to understand how the candidate works with AI.

    Returns:
        - action_chains: classified prompt→response→action sequences
        - temporal_progression: how prompt quality changes over time
        - workflow_patterns: exploration→coding→testing patterns
        - adaptation_score: how much they modify AI output (from modificationDepth)
    """
    if not interactions:
        return _empty_result()

    sorted_events = sorted(interactions, key=lambda e: e.get("timestamp", ""))

    chains = _build_action_chains(sorted_events)
    temporal = _analyze_temporal_progression(sorted_events)
    workflow = _analyze_workflow_patterns(sorted_events)
    adaptation = _analyze_adaptation(sorted_events)

    # Compute overall fluency indicators from chains
    chain_summary = _summarize_chains(chains)

    return {
        "actionChains": chains,
        "chainSummary": chain_summary,
        "temporalProgression": temporal,
        "workflowPatterns": workflow,
        "adaptationScore": adaptation,
    }


# ─── Action chain builder ─────────────────────────────────────────────────────

def _build_action_chains(events: List[Dict]) -> List[Dict[str, Any]]:
    """
    Build prompt→response→action chains.

    For each AI prompt, find what happened next:
    - pasted verbatim? modified? ran tests? asked follow-up? wrote own code?
    """
    chains = []
    prompts = [(i, e) for i, e in enumerate(events) if e.get("event_type") == "prompt_sent"]

    for idx, (event_idx, prompt_event) in enumerate(prompts):
        prompt_text = prompt_event.get("prompt_text", "")
        prompt_ts = prompt_event.get("timestamp", "")

        # Find the AI response (next response_received after this prompt)
        response_event = None
        response_text = ""
        for j in range(event_idx + 1, min(event_idx + 10, len(events))):
            if events[j].get("event_type") == "response_received":
                response_event = events[j]
                response_text = events[j].get("response_text", "") or ""
                break

        # Find what happened in the next 3 minutes after the prompt
        actions_after = []
        window_end = event_idx + 30  # max 30 events forward
        if window_end > len(events):
            window_end = len(events)

        # Also stop at the next prompt
        next_prompt_idx = prompts[idx + 1][0] if idx + 1 < len(prompts) else len(events)
        window_end = min(window_end, next_prompt_idx)

        for j in range(event_idx + 1, window_end):
            e = events[j]
            etype = e.get("event_type", "")
            if etype in ("response_received",):
                continue  # skip the response itself
            ts_diff = _time_diff(prompt_ts, e.get("timestamp"))
            if ts_diff and ts_diff > 180:
                break  # stop after 3 minutes
            actions_after.append({
                "eventType": etype,
                "secondsAfterPrompt": round(ts_diff, 1) if ts_diff else None,
                "metadata": _safe_metadata(e),
            })

        # Classify the chain
        chain_type = _classify_chain(prompt_text, response_text, actions_after)

        chains.append({
            "promptText": prompt_text[:200],
            "promptCategory": _classify_prompt(prompt_text),
            "responseLength": len(response_text),
            "actionsAfter": actions_after[:10],  # cap for payload size
            "chainType": chain_type,
            "timestamp": prompt_ts,
        })

    return chains


def _classify_chain(prompt_text: str, response_text: str, actions: List[Dict]) -> str:
    """
    Classify what happened after this AI interaction.

    Returns one of:
    - "verified": pasted/modified then ran tests
    - "adapted": pasted then modified significantly
    - "blind_paste": pasted without modification
    - "reference_only": read response but didn't paste, wrote own code
    - "rejected": pasted then undid / deleted
    - "follow_up": asked another question (debugging chain)
    - "no_action": nothing happened
    """
    action_types = [a["eventType"] for a in actions]

    has_paste = any(t in ("code_pasted_from_ai",) for t in action_types)
    has_modification = any(t == "code_modified" for t in action_types)
    has_test_run = any(
        t == "command_executed" and _is_test_command(a.get("metadata", {}))
        for t, a in zip(action_types, actions)
    )
    has_follow_up_prompt = any(t == "prompt_sent" for t in action_types)
    has_file_delete = any(t == "file_deleted" for t in action_types)

    # Check modification depth if available
    mod_depths = []
    for a in actions:
        if a["eventType"] == "code_modified":
            md = (a.get("metadata") or {}).get("modificationDepth")
            if md is not None:
                mod_depths.append(float(md))

    avg_mod_depth = sum(mod_depths) / len(mod_depths) if mod_depths else 0

    if has_paste and has_test_run:
        return "verified"
    if has_paste and has_modification and avg_mod_depth >= 5:
        return "adapted"
    if has_paste and has_modification and avg_mod_depth < 5:
        return "light_edit"
    if has_paste and has_file_delete:
        return "rejected"
    if has_paste and not has_modification:
        return "blind_paste"
    if not has_paste and has_modification:
        return "reference_only"
    if has_follow_up_prompt and not has_paste:
        return "follow_up"
    return "no_action"


def _classify_prompt(text: str) -> str:
    """
    Classify prompt intent into categories:
    - "solution_request": asking for full implementation
    - "debugging": asking about a specific error/issue
    - "explanation": asking to understand something
    - "hypothesis": stating a theory and asking for confirmation
    - "targeted": asking about a specific function/line/concept
    - "broad": vague or general request
    """
    text_lower = text.lower().strip()

    if re.search(r"i think|i believe|could it be|is it because|my guess", text_lower):
        return "hypothesis"
    if re.search(r"solve|complete|write.*code|implement|create|build.*for me|give.*full|do.*whole", text_lower):
        return "solution_request"
    if re.search(r"debug|fix|error|bug|why.*not.*work|issue|broken|failing|crash", text_lower):
        return "debugging"
    if re.search(r"explain|how does|why does|what does|what is|understand|tell me about", text_lower):
        return "explanation"
    if re.search(r"line \d|function \w|in file|this code|this component|useeffect|usestate|router\.|app\.", text_lower):
        return "targeted"
    return "broad"


# ─── Temporal progression ──────────────────────────────────────────────────────

def _analyze_temporal_progression(events: List[Dict]) -> Dict[str, Any]:
    """
    Check: do prompts get smarter over time?
    Split session into thirds and compare prompt quality.
    """
    prompts = [e for e in events if e.get("event_type") == "prompt_sent"]
    if len(prompts) < 3:
        return {"progression": "insufficient_data", "thirds": []}

    third = len(prompts) // 3
    thirds = [
        prompts[:third],
        prompts[third:2 * third],
        prompts[2 * third:],
    ]

    third_analysis = []
    for i, group in enumerate(thirds):
        categories = [_classify_prompt(p.get("prompt_text", "")) for p in group]
        third_analysis.append({
            "period": ["early", "middle", "late"][i],
            "promptCount": len(group),
            "categories": {cat: categories.count(cat) for cat in set(categories)},
            "sophisticationScore": _prompt_sophistication_score(categories),
        })

    # Did they improve?
    early_score = third_analysis[0]["sophisticationScore"]
    late_score = third_analysis[-1]["sophisticationScore"]

    if late_score > early_score + 1:
        progression = "improving"
    elif late_score < early_score - 1:
        progression = "declining"
    else:
        progression = "stable"

    return {
        "progression": progression,
        "thirds": third_analysis,
        "earlyScore": early_score,
        "lateScore": late_score,
    }


def _prompt_sophistication_score(categories: List[str]) -> float:
    """Score prompt sophistication (0-10). Higher = more targeted/hypothesis-driven."""
    weights = {
        "hypothesis": 10,
        "debugging": 7,
        "targeted": 6,
        "explanation": 5,
        "broad": 2,
        "solution_request": 1,
    }
    if not categories:
        return 0
    return round(sum(weights.get(c, 3) for c in categories) / len(categories), 1)


# ─── Workflow patterns ─────────────────────────────────────────────────────────

def _analyze_workflow_patterns(events: List[Dict]) -> Dict[str, Any]:
    """
    What did the candidate do first? Did they explore before coding?
    """
    if not events:
        return {"firstAction": "none", "exploredFirst": False, "ranTestsBeforeFixes": False}

    # First 5 events
    first_actions = [e.get("event_type", "") for e in events[:min(5, len(events))]]

    explored_first = any(t in ("file_created", "file_modified") for t in first_actions[:3]) is False
    # Check: did they run tests early?
    early_test_run = False
    for e in events[:min(15, len(events))]:
        if e.get("event_type") == "command_executed":
            meta = e.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    import json
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            cmd = meta.get("command", "")
            if _is_test_command_str(cmd):
                early_test_run = True
                break

    return {
        "firstActions": first_actions[:5],
        "exploredFirst": explored_first,
        "ranTestsEarly": early_test_run,
    }


# ─── Adaptation analysis ──────────────────────────────────────────────────────

def _analyze_adaptation(events: List[Dict]) -> Dict[str, Any]:
    """
    Use the modificationDepth metadata (0-10) that the frontend already computes.
    """
    modifications = [
        e for e in events
        if e.get("event_type") == "code_modified"
    ]

    depths = []
    for mod in modifications:
        meta = mod.get("metadata") or {}
        if isinstance(meta, str):
            try:
                import json
                meta = json.loads(meta)
            except Exception:
                meta = {}
        depth = meta.get("modificationDepth")
        if depth is not None:
            depths.append(float(depth))

    if not depths:
        return {"averageDepth": 0, "totalModifications": 0, "assessment": "no_data"}

    avg = sum(depths) / len(depths)
    high_mods = sum(1 for d in depths if d >= 7)
    low_mods = sum(1 for d in depths if d <= 2)

    if avg >= 6:
        assessment = "heavy_adapter"  # rewrites AI code significantly
    elif avg >= 3:
        assessment = "moderate_adapter"  # makes meaningful changes
    elif avg >= 1:
        assessment = "light_adapter"  # small tweaks only
    else:
        assessment = "verbatim_paster"  # doesn't change AI code

    return {
        "averageDepth": round(avg, 1),
        "totalModifications": len(depths),
        "highDepthModifications": high_mods,
        "lowDepthModifications": low_mods,
        "assessment": assessment,
    }


# ─── Chain summary ─────────────────────────────────────────────────────────────

def _summarize_chains(chains: List[Dict]) -> Dict[str, Any]:
    """Summarize action chain types into a fluency profile."""
    if not chains:
        return {"totalChains": 0, "fluencyScore": 0}

    type_counts = {}
    for c in chains:
        ct = c.get("chainType", "no_action")
        type_counts[ct] = type_counts.get(ct, 0) + 1

    total = len(chains)

    # Fluency score: reward verification/adaptation/reference, penalize blind paste
    weights = {
        "verified": 10,
        "adapted": 8,
        "reference_only": 9,
        "rejected": 7,  # recognizing bad AI output is good
        "light_edit": 5,
        "follow_up": 4,
        "blind_paste": 1,
        "no_action": 3,
    }

    fluency_score = round(
        sum(weights.get(c.get("chainType", "no_action"), 3) for c in chains) / total,
        1,
    )

    return {
        "totalChains": total,
        "chainTypes": type_counts,
        "fluencyScore": fluency_score,
        "verifiedRate": round(type_counts.get("verified", 0) / total, 2),
        "blindPasteRate": round(type_counts.get("blind_paste", 0) / total, 2),
        "adaptedRate": round((type_counts.get("adapted", 0) + type_counts.get("light_edit", 0)) / total, 2),
        "referenceOnlyRate": round(type_counts.get("reference_only", 0) / total, 2),
    }


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _is_test_command(meta: Any) -> bool:
    if isinstance(meta, str):
        try:
            import json
            meta = json.loads(meta)
        except Exception:
            return False
    if not isinstance(meta, dict):
        return False
    cmd = meta.get("command", "")
    return _is_test_command_str(cmd)


def _is_test_command_str(cmd: str) -> bool:
    cmd_lower = cmd.lower()
    return any(t in cmd_lower for t in ["npm test", "npm run test", "vitest", "jest", "pytest", "npx vitest"])


def _safe_metadata(event: Dict) -> Optional[Dict]:
    meta = event.get("metadata")
    if isinstance(meta, str):
        try:
            import json
            return json.loads(meta)
        except Exception:
            return {}
    return meta if isinstance(meta, dict) else {}


def _time_diff(ts1: Any, ts2: Any) -> Optional[float]:
    try:
        if isinstance(ts1, str):
            from dateutil.parser import parse
            ts1 = parse(ts1)
        if isinstance(ts2, str):
            from dateutil.parser import parse
            ts2 = parse(ts2)
        if isinstance(ts1, datetime) and isinstance(ts2, datetime):
            diff = (ts2 - ts1).total_seconds()
            return diff if diff >= 0 else None
    except Exception:
        pass
    return None


def _empty_result() -> Dict[str, Any]:
    return {
        "actionChains": [],
        "chainSummary": {"totalChains": 0, "fluencyScore": 0},
        "temporalProgression": {"progression": "no_data"},
        "workflowPatterns": {"firstAction": "none"},
        "adaptationScore": {"averageDepth": 0, "assessment": "no_data"},
    }
