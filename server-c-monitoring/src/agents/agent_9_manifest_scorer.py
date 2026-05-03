"""
Agent 9: Manifest-Aware Scorer (v2 — Deep Fluency Analysis)

Scores candidate work against the assessment manifest (canonical contract from Server B).

v2 changes:
- Uses codeBefore/codeAfter diffs (not just final code keyword matching)
- Builds prompt→response→action chains (sequence analysis)
- Correlates terminal events (test runs, dev server, debugging)
- Produces per-bug narratives (story of how each bug was handled)
- Analyzes AI response adoption (verbatim paste vs adaptation)
- Computes temporal progression (did prompts get smarter over time?)

The goal: understand HOW the candidate works with AI, not just WHAT they produced.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import DatabaseAPIClient

# Import analyzers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyzers.sequence_analyzer import analyze_sequences
from analyzers.diff_analyzer import analyze_diffs
from analyzers.terminal_analyzer import analyze_terminal
from analyzers.response_analyzer import analyze_responses
from analyzers.bug_narrative import build_bug_narratives

logger = logging.getLogger(__name__)


async def score_with_manifest(
    session_id: str,
    manifest: Dict[str, Any],
    final_files: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Score a candidate session against the assessment manifest.

    This is the v2 scorer — it uses deep analysis instead of keyword matching.

    Args:
        session_id: Session ID to score
        manifest: The assessmentManifest from Server B output
        final_files: Optional dict of {filepath: content} for candidate's final code.
                     If not provided, reconstructed from code snapshots.

    Returns:
        Structured score report with per-dimension scores, per-bug narratives,
        fluency analysis, and overall score.
    """
    try:
        logger.info(f"[v2] Scoring session {session_id} (type={manifest.get('assessmentType')})")

        db_client = DatabaseAPIClient()

        # ── Fetch all data ──────────────────────────────────────────────
        interactions = db_client.get_interactions(session_id)
        submissions = db_client.get_submissions(session_id)

        if not final_files:
            final_files = _reconstruct_final_files(db_client, session_id)

        logger.info(
            f"  Data: {len(interactions)} interactions, {len(submissions)} submissions, "
            f"{len(final_files)} final files"
        )

        # ── Run all 4 analyzers ─────────────────────────────────────────
        injected_bug_ids = manifest.get("injectedBugIds", [])
        expected_signals = manifest.get("expectedSignals", {})

        # 1. Sequence analysis (prompt→response→action chains)
        sequence_result = analyze_sequences(interactions)

        # 2. Diff analysis (codeBefore/codeAfter per bug)
        diff_result = analyze_diffs(interactions, injected_bug_ids, expected_signals)

        # 3. Terminal analysis (test runs, dev server, debugging)
        terminal_result = analyze_terminal(interactions)

        # 4. Response analysis (AI adoption patterns)
        response_result = analyze_responses(interactions)

        # ── Build per-bug narratives ────────────────────────────────────
        bug_narratives = build_bug_narratives(
            injected_bug_ids=injected_bug_ids,
            expected_signals=expected_signals,
            diff_evidence=diff_result.get("bugEvidence", {}),
            sequence_chains=sequence_result.get("actionChains", []),
            terminal_analysis=terminal_result,
            interactions=interactions,
            final_files=final_files,
        )

        # ── Compute dimension scores ────────────────────────────────────
        rubric = manifest.get("scoringRubric", {})
        dimension_scores = _compute_dimensions(
            rubric=rubric,
            bug_narratives=bug_narratives,
            sequence_result=sequence_result,
            diff_result=diff_result,
            terminal_result=terminal_result,
            response_result=response_result,
            interactions=interactions,
            submissions=submissions,
            manifest=manifest,
            final_files=final_files,
        )

        # ── Calculate overall score ─────────────────────────────────────
        overall_score = _compute_overall_score(dimension_scores)

        # ── Generate insights ───────────────────────────────────────────
        strengths, weaknesses = _generate_insights(
            dimension_scores, bug_narratives,
            sequence_result, terminal_result, response_result,
        )

        # ── Confidence ──────────────────────────────────────────────────
        confidence = _compute_confidence(interactions, final_files, diff_result)

        # ── Bug discovery summary (backward compatible) ─────────────────
        bug_summary = _summarize_bugs(bug_narratives)

        # ── Build candidate-facing explanation ──────────────────────────
        explanation = _build_explanation(
            overall_score, bug_summary, sequence_result, terminal_result,
        )

        return {
            "success": True,
            "sessionId": session_id,
            "scorerVersion": "v2",
            "assessmentType": manifest.get("assessmentType", "unknown"),
            "role": manifest.get("role", "unknown"),
            "overallScore": overall_score,
            "dimensionScores": dimension_scores,

            # Deep analysis results
            "bugNarratives": bug_narratives,
            "bugDiscovery": bug_summary,
            "fluencyAnalysis": {
                "chainSummary": sequence_result.get("chainSummary", {}),
                "temporalProgression": sequence_result.get("temporalProgression", {}),
                "workflowPatterns": sequence_result.get("workflowPatterns", {}),
                "adaptationScore": sequence_result.get("adaptationScore", {}),
            },
            "responseAnalysis": {
                "usagePattern": response_result.get("usagePattern", {}),
                "adoptionPatterns": response_result.get("adoptionPatterns", {}),
                "responseQuality": response_result.get("responseQuality", {}),
            },
            "terminalAnalysis": {
                "testBehavior": terminal_result.get("testBehavior", {}),
                "engagementScore": terminal_result.get("engagementScore", {}),
                "devServer": terminal_result.get("devServer", {}),
            },
            "codeOrigins": diff_result.get("codeOrigins", {}),
            "fileChangeMap": diff_result.get("fileChangeMap", {}),

            # Summary
            "strengths": strengths,
            "weaknesses": weaknesses,
            "confidence": confidence,
            "explanation": explanation,

            # Backward-compatible fields
            "checkpointResults": _score_checkpoints(
                manifest.get("checkpoints", []), submissions, interactions,
            ),
            "behaviorAnalysis": _legacy_behavior(sequence_result, response_result),
            "codeQuality": _score_code_quality(final_files),
        }

    except Exception as e:
        logger.error(f"Error scoring with manifest: {e}", exc_info=True)
        return {
            "success": False,
            "sessionId": session_id,
            "scorerVersion": "v2",
            "overallScore": 0,
            "explanation": f"Scoring error: {str(e)}",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DIMENSION SCORING
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_dimensions(
    rubric: Dict,
    bug_narratives: Dict,
    sequence_result: Dict,
    diff_result: Dict,
    terminal_result: Dict,
    response_result: Dict,
    interactions: List[Dict],
    submissions: List[Dict],
    manifest: Dict,
    final_files: Dict,
) -> Dict[str, Any]:
    """
    Compute per-dimension scores from all analyzer outputs.

    Each dimension maps to a specific signal from the analyzers.
    """
    # Extract key metrics from analyzers
    chain_summary = sequence_result.get("chainSummary", {})
    temporal = sequence_result.get("temporalProgression", {})
    adaptation = sequence_result.get("adaptationScore", {})
    code_origins = diff_result.get("codeOrigins", {})
    test_behavior = terminal_result.get("testBehavior", {})
    engagement = terminal_result.get("engagementScore", {})
    adoption = response_result.get("adoptionPatterns", {})
    usage_pattern = response_result.get("usagePattern", {})

    # Bug narrative scores
    bug_scores = [n.get("score", 0) for n in bug_narratives.values()]
    avg_bug_score = sum(bug_scores) / len(bug_scores) if bug_scores else 0
    bugs_found = sum(1 for n in bug_narratives.values() if n.get("discovery", {}).get("discovered"))
    bugs_fixed = sum(1 for n in bug_narratives.values() if n.get("finalFixed"))
    total_bugs = len(bug_narratives)

    # Raw score computation per dimension
    raw_scores = {
        "bug_discovery": (bugs_found / max(total_bugs, 1)) * 10,
        "fix_correctness": (bugs_fixed / max(total_bugs, 1)) * 10,
        "checkpoint_completion": _get_checkpoint_score(
            manifest.get("checkpoints", []), submissions, interactions,
        ),
        "ai_reliance": _compute_ai_reliance_score(
            chain_summary, adoption, code_origins,
        ),
        "blind_trust_detection": _compute_blind_trust_score(
            chain_summary, adoption, adaptation,
        ),
        "code_quality": _compute_quality_score(final_files, test_behavior),
        # Role-specific dimensions (used if present in rubric)
        "security_awareness": _compute_security_score(bug_narratives),
        "data_validation": _compute_data_validation_score(bug_narratives),
        "communication": _compute_communication_score(
            submissions, interactions, temporal,
        ),
        # New fluency dimensions
        "process_quality": _compute_process_score(
            chain_summary, test_behavior, engagement, temporal,
        ),
        "verification_habits": _compute_verification_score(
            chain_summary, test_behavior, bug_narratives,
        ),
    }

    # Apply rubric weights
    dimension_scores = {}
    for dim_name, dim_config in rubric.items():
        weight = dim_config.get("weight", 0)
        max_score = dim_config.get("maxScore", 10)
        raw = min(raw_scores.get(dim_name, 5), max_score)

        dimension_scores[dim_name] = {
            "weight": weight,
            "max_score": max_score,
            "raw_score": round(raw, 1),
            "weighted_score": round(raw * weight, 2),
        }

    return dimension_scores


def _compute_ai_reliance_score(
    chain_summary: Dict, adoption: Dict, code_origins: Dict,
) -> float:
    """
    Score AI reliance (0-10). Higher = healthier AI usage.

    Signals:
    - Low blind paste rate = good
    - High verified/adapted rate = good
    - Balanced code origin = good
    """
    score = 5.0  # baseline

    # Blind paste penalty
    blind_rate = chain_summary.get("blindPasteRate", 0)
    score -= blind_rate * 4  # up to -4

    # Verification reward
    verified_rate = chain_summary.get("verifiedRate", 0)
    score += verified_rate * 3  # up to +3

    # Adaptation reward
    adapted_rate = chain_summary.get("adaptedRate", 0)
    score += adapted_rate * 2  # up to +2

    # Verbatim paste penalty from response analysis
    verbatim_rate = adoption.get("verbatimRate", 0)
    score -= verbatim_rate * 2  # up to -2

    # Code origin balance
    ai_ratio = code_origins.get("aiCodeRatio", 0.5)
    if 0.2 <= ai_ratio <= 0.6:
        score += 1  # balanced use
    elif ai_ratio > 0.8:
        score -= 2  # almost all AI code

    return max(0, min(10, round(score, 1)))


def _compute_blind_trust_score(
    chain_summary: Dict, adoption: Dict, adaptation: Dict,
) -> float:
    """
    Score blind trust detection (0-10). Higher = less blind trust = better.
    """
    score = 5.0

    blind_rate = chain_summary.get("blindPasteRate", 0)
    score -= blind_rate * 5

    verbatim_rate = adoption.get("verbatimRate", 0)
    score -= verbatim_rate * 3

    # Reward adaptation
    avg_depth = adaptation.get("averageDepth", 0)
    if avg_depth >= 5:
        score += 3
    elif avg_depth >= 3:
        score += 1.5

    return max(0, min(10, round(score, 1)))


def _compute_quality_score(final_files: Dict, test_behavior: Dict) -> float:
    """Score code quality with richer signals."""
    if not final_files:
        return 0

    score = 4.0  # baseline

    total_lines = 0
    has_tests = False
    has_error_handling = False
    has_types = False

    for path, content in final_files.items():
        if not isinstance(content, str):
            continue
        lines = content.split("\n")
        total_lines += len(lines)

        if "test" in path.lower() or "spec" in path.lower():
            has_tests = True
        if "catch" in content or "try" in content:
            has_error_handling = True
        if "interface " in content or ": string" in content or "TypeScript" in content:
            has_types = True

    if has_tests:
        score += 1.5
    if has_error_handling:
        score += 1
    if has_types:
        score += 1

    # Testing behavior from terminal analysis
    test_assess = test_behavior.get("assessment", "never_tested")
    test_bonus = {
        "test_driven": 2.5,
        "iterative_testing": 2,
        "occasional_testing": 1,
        "single_check": 0.5,
        "baseline_only": 0.3,
        "never_tested": 0,
    }
    score += test_bonus.get(test_assess, 0)

    return max(0, min(10, round(score, 1)))


def _compute_security_score(bug_narratives: Dict) -> float:
    """Score security awareness from bug narratives."""
    security_bugs = ["bug_sql_injection", "bug_auth_missing", "bug_auth_not_wired", "bug_no_rate_limit"]
    found = 0
    fixed = 0
    total = 0

    for bug_id, narrative in bug_narratives.items():
        if bug_id in security_bugs:
            total += 1
            if narrative.get("discovery", {}).get("discovered"):
                found += 1
            if narrative.get("finalFixed"):
                fixed += 1

    if total == 0:
        return 5.0  # neutral — no security bugs in this assessment

    return round((found * 0.3 + fixed * 0.7) / total * 10, 1)


def _compute_data_validation_score(bug_narratives: Dict) -> float:
    """Score data validation awareness."""
    data_bugs = ["bug_missing_validation", "bug_no_404", "bug_error_handler_200", "bug_spec_mismatch"]
    found = 0
    fixed = 0
    total = 0

    for bug_id, narrative in bug_narratives.items():
        if bug_id in data_bugs:
            total += 1
            if narrative.get("discovery", {}).get("discovered"):
                found += 1
            if narrative.get("finalFixed"):
                fixed += 1

    if total == 0:
        return 5.0

    return round((found * 0.3 + fixed * 0.7) / total * 10, 1)


def _compute_communication_score(
    submissions: List[Dict], interactions: List[Dict], temporal: Dict,
) -> float:
    """Score communication quality from submissions and prompt progression."""
    score = 4.0

    # Did they write explanations in submissions?
    for sub in submissions:
        notes = sub.get("notes", "") or ""
        if len(notes) > 50:
            score += 1
        if len(notes) > 200:
            score += 1

    # Temporal progression: improving prompts is a communication signal
    progression = temporal.get("progression", "no_data")
    if progression == "improving":
        score += 2
    elif progression == "stable":
        score += 0.5

    return max(0, min(10, round(score, 1)))


def _compute_process_score(
    chain_summary: Dict, test_behavior: Dict,
    engagement: Dict, temporal: Dict,
) -> float:
    """
    Score the candidate's overall development process.
    Verified chains + test-driven + improving prompts = great process.
    """
    score = 3.0

    # Chain quality
    fluency = chain_summary.get("fluencyScore", 0)
    score += min(3, fluency / 3)  # up to +3

    # Testing
    test_assess = test_behavior.get("assessment", "never_tested")
    if test_assess in ("test_driven", "iterative_testing"):
        score += 2
    elif test_assess in ("occasional_testing",):
        score += 1

    # Engagement
    eng_score = engagement.get("score", 0)
    score += min(2, eng_score / 50)  # up to +2

    return max(0, min(10, round(score, 1)))


def _compute_verification_score(
    chain_summary: Dict, test_behavior: Dict, bug_narratives: Dict,
) -> float:
    """Score verification habits."""
    score = 3.0

    # How many bugs were verified after fixing?
    verified_count = sum(
        1 for n in bug_narratives.values()
        if n.get("verification", {}).get("verified")
    )
    total = max(len(bug_narratives), 1)
    score += (verified_count / total) * 4

    # Chain verification rate
    verified_rate = chain_summary.get("verifiedRate", 0)
    score += verified_rate * 3

    return max(0, min(10, round(score, 1)))


def _get_checkpoint_score(
    checkpoints: List[Dict], submissions: List[Dict], interactions: List[Dict],
) -> float:
    """Compute checkpoint completion rate as 0-10 score."""
    result = _score_checkpoints(checkpoints, submissions, interactions)
    return round(result.get("completionRate", 0) * 10, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# OVERALL SCORE
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_overall_score(dimension_scores: Dict) -> float:
    """Weighted average of all dimensions, normalized to 0-100."""
    total_weight = sum(d.get("weight", 0) for d in dimension_scores.values())
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(d["weighted_score"] for d in dimension_scores.values())
    max_possible = sum(d["max_score"] * d["weight"] for d in dimension_scores.values())

    if max_possible == 0:
        return 0.0

    return round(weighted_sum / max_possible * 100, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_insights(
    dimension_scores: Dict,
    bug_narratives: Dict,
    sequence_result: Dict,
    terminal_result: Dict,
    response_result: Dict,
) -> tuple:
    """Generate strengths and weaknesses from all analysis."""
    strengths = []
    weaknesses = []

    # Dimension-based
    for dim_name, dim_data in dimension_scores.items():
        pct = (dim_data["raw_score"] / dim_data["max_score"] * 100) if dim_data["max_score"] > 0 else 0
        label = dim_name.replace("_", " ").title()
        if pct >= 70:
            strengths.append(f"{label}: strong ({pct:.0f}%)")
        elif pct < 35:
            weaknesses.append(f"{label}: needs improvement ({pct:.0f}%)")

    # Fluency-based insights
    chain_summary = sequence_result.get("chainSummary", {})
    if chain_summary.get("verifiedRate", 0) > 0.3:
        strengths.append("Frequently verifies AI output before committing")
    if chain_summary.get("blindPasteRate", 0) > 0.4:
        weaknesses.append("High blind paste rate — applies AI code without review")

    # Temporal progression
    temporal = sequence_result.get("temporalProgression", {})
    if temporal.get("progression") == "improving":
        strengths.append("Prompts improved in quality over the session")
    elif temporal.get("progression") == "declining":
        weaknesses.append("Prompt quality declined during the session")

    # Terminal
    test_assess = terminal_result.get("testBehavior", {}).get("assessment", "")
    if test_assess == "test_driven":
        strengths.append("Test-driven approach: ran tests before and after changes")
    elif test_assess == "never_tested":
        weaknesses.append("Never ran tests during the assessment")

    # Response adoption
    adoption = response_result.get("adoptionPatterns", {})
    if adoption.get("verbatimRate", 0) > 0.5:
        weaknesses.append("Majority of AI code pasted verbatim without modification")
    if adoption.get("adaptedRate", 0) > 0.4:
        strengths.append("Consistently adapts AI suggestions before applying")

    # Bug-specific insights
    missed_security = []
    for bug_id, narrative in bug_narratives.items():
        if not narrative.get("discovery", {}).get("discovered"):
            if "sql" in bug_id or "auth" in bug_id:
                missed_security.append(bug_id.replace("bug_", "").replace("_", " "))
    if missed_security:
        weaknesses.append(f"Missed security issues: {', '.join(missed_security)}")

    return strengths[:8], weaknesses[:8]


# ═══════════════════════════════════════════════════════════════════════════════
# BACKWARD-COMPATIBLE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _summarize_bugs(narratives: Dict) -> Dict[str, Any]:
    """Backward-compatible bug discovery summary."""
    found = []
    fixed = []
    missed = []

    for bug_id, n in narratives.items():
        if n.get("finalFixed"):
            fixed.append(bug_id)
            found.append(bug_id)
        elif n.get("discovery", {}).get("discovered"):
            found.append(bug_id)
        else:
            missed.append(bug_id)

    total = max(len(narratives), 1)
    return {
        "totalBugs": len(narratives),
        "bugsFound": len(found),
        "bugsFixed": len(fixed),
        "bugsMissed": len(missed),
        "discoveryRate": round(len(found) / total, 2),
        "fixRate": round(len(fixed) / total, 2),
        "details": {"found": found, "fixed": fixed, "missed": missed},
    }


def _score_checkpoints(
    checkpoints: List[Dict],
    submissions: List[Dict],
    interactions: List[Dict],
) -> Dict[str, Any]:
    """Score checkpoint completions (unchanged from v1)."""
    results = []
    completed = 0

    all_text = " ".join(
        (s.get("code", "") or "") + " " + (s.get("notes", "") or "")
        for s in submissions
    )
    all_text += " " + " ".join(
        (i.get("prompt_text", "") or "")
        for i in interactions
        if i.get("event_type") == "prompt_sent"
    )
    all_text_lower = all_text.lower()

    for cp in checkpoints:
        cp_id = cp.get("id", "")
        cp_prompt = cp.get("prompt", "")
        keywords = [w.lower() for w in cp_prompt.split() if len(w) > 3][:5]

        addressed = sum(1 for kw in keywords if kw in all_text_lower)
        score = min(1.0, addressed / max(len(keywords), 1))

        if score > 0.4:
            completed += 1

        results.append({
            "checkpointId": cp_id,
            "prompt": cp_prompt,
            "score": round(score, 2),
            "addressed": score > 0.4,
        })

    total = len(checkpoints) if checkpoints else 1
    return {
        "totalCheckpoints": len(checkpoints),
        "completed": completed,
        "completionRate": round(completed / total, 2),
        "details": results,
    }


def _legacy_behavior(sequence_result: Dict, response_result: Dict) -> Dict[str, Any]:
    """Backward-compatible behavior analysis."""
    chain_summary = sequence_result.get("chainSummary", {})
    usage_pattern = response_result.get("usagePattern", {})
    adaptation = sequence_result.get("adaptationScore", {})

    # Map new scores to old format
    blind_paste_rate = chain_summary.get("blindPasteRate", 0)
    fluency_score = chain_summary.get("fluencyScore", 5)

    # Convert fluency score (1-10) to behavior score (0-100)
    behavior_score = int(fluency_score * 10)

    assessment = (
        "high_reliance" if blind_paste_rate > 0.5
        else "moderate_reliance" if blind_paste_rate > 0.2
        else "healthy_usage"
    )

    return {
        "behaviorScore": behavior_score,
        "totalPrompts": chain_summary.get("totalChains", 0),
        "blindTrustRatio": round(blind_paste_rate, 2),
        "promptBreakdown": usage_pattern.get("breakdown", {}),
        "assessment": assessment,
        "adaptationDepth": adaptation.get("averageDepth", 0),
        "adaptationAssessment": adaptation.get("assessment", "no_data"),
    }


def _score_code_quality(final_files: Dict[str, str]) -> Dict[str, Any]:
    """Basic code quality assessment (backward compatible)."""
    if not final_files:
        return {"score": 0, "totalFiles": 0, "totalLines": 0}

    total_lines = 0
    total_comments = 0
    total_files = len(final_files)
    has_tests = False
    has_error_handling = False

    for path, content in final_files.items():
        if not isinstance(content, str):
            continue
        lines = content.split("\n")
        total_lines += len(lines)
        total_comments += sum(1 for line in lines if line.strip().startswith(("//", "#", "/*", "*")))

        if "test" in path.lower() or "spec" in path.lower():
            has_tests = True
        if "catch" in content or "try" in content or "except" in content:
            has_error_handling = True

    score = 50
    if has_tests:
        score += 15
    if has_error_handling:
        score += 10
    if total_comments > 5:
        score += 10
    if total_lines > 100:
        score += 15

    return {
        "score": min(100, score),
        "totalFiles": total_files,
        "totalLines": total_lines,
        "totalComments": total_comments,
        "hasTests": has_tests,
        "hasErrorHandling": has_error_handling,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _reconstruct_final_files(db_client: DatabaseAPIClient, session_id: str) -> Dict[str, str]:
    """Reconstruct final files from code snapshots."""
    snapshots = db_client.get_code_snapshots(session_id)
    if not snapshots:
        return {}

    latest = snapshots[-1]
    code = latest.get("code", "")
    try:
        files = json.loads(code)
        if isinstance(files, dict):
            return files
    except (json.JSONDecodeError, TypeError):
        pass

    return {"main": code}


def _compute_confidence(
    interactions: List[Dict], final_files: Dict, diff_result: Dict,
) -> int:
    """
    Confidence in the score (0-100).
    More data + richer signals = higher confidence.
    """
    confidence = 20  # baseline

    # Interaction volume
    if len(interactions) >= 10:
        confidence += 15
    elif len(interactions) >= 5:
        confidence += 8

    # Final files
    if final_files:
        confidence += min(15, len(final_files) * 2)

    # Diff events (codeBefore/codeAfter) — rich signals
    diff_count = diff_result.get("totalDiffEvents", 0)
    if diff_count >= 5:
        confidence += 20
    elif diff_count >= 2:
        confidence += 10

    # Code origins (we have paste vs self-write data)
    origins = diff_result.get("codeOrigins", {})
    if origins.get("totalModifications", 0) > 0:
        confidence += 10

    # Total code volume
    total_code = sum(len(v) for v in final_files.values() if isinstance(v, str))
    if total_code > 1000:
        confidence += 10

    return min(100, confidence)


def _build_explanation(
    overall_score: float,
    bug_summary: Dict,
    sequence_result: Dict,
    terminal_result: Dict,
) -> str:
    """Build a human-readable scoring explanation."""
    parts = []

    # Overall
    parts.append(f"Overall score: {overall_score}/100.")

    # Bugs
    total = bug_summary.get("totalBugs", 0)
    found = bug_summary.get("bugsFound", 0)
    fixed = bug_summary.get("bugsFixed", 0)
    parts.append(f"Found {found}/{total} injected issues, fixed {fixed}.")

    # Fluency
    chain_summary = sequence_result.get("chainSummary", {})
    fluency = chain_summary.get("fluencyScore", 0)
    if fluency >= 7:
        parts.append("Strong AI fluency — verifies and adapts AI output.")
    elif fluency >= 4:
        parts.append("Moderate AI fluency — some adaptation, room for more verification.")
    else:
        parts.append("Low AI fluency — tends to paste AI output without review.")

    # Testing
    test_assess = terminal_result.get("testBehavior", {}).get("assessment", "")
    if test_assess == "test_driven":
        parts.append("Excellent testing approach.")
    elif test_assess == "never_tested":
        parts.append("Did not run tests during the assessment.")

    return " ".join(parts)
