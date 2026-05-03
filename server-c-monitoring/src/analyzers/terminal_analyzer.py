"""
Terminal Analyzer
Correlates terminal events with the candidate's workflow.

Key questions:
- Did they run tests? When? How often?
- Did they run tests BEFORE or AFTER fixing bugs?
- Did they use dev server? Did they check for errors?
- Did they install new packages?
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def analyze_terminal(interactions: List[Dict]) -> Dict[str, Any]:
    """
    Analyze terminal events to understand test/build/debug behavior.
    """
    terminal_events = [
        e for e in interactions
        if e.get("event_type") in ("command_executed", "terminal_spawned")
    ]

    if not terminal_events:
        return _empty_result()

    commands = _extract_commands(terminal_events)
    test_analysis = _analyze_test_behavior(commands, interactions)
    dev_server = _analyze_dev_server(commands)
    package_installs = _analyze_package_installs(commands)
    debug_commands = _analyze_debug_commands(commands)

    # Overall terminal engagement score
    engagement = _compute_engagement(test_analysis, dev_server, debug_commands)

    return {
        "totalCommands": len(commands),
        "commands": commands[:50],  # cap for payload size
        "testBehavior": test_analysis,
        "devServer": dev_server,
        "packageInstalls": package_installs,
        "debugCommands": debug_commands,
        "engagementScore": engagement,
    }


# ─── Command extraction ───────────────────────────────────────────────────────

def _extract_commands(terminal_events: List[Dict]) -> List[Dict[str, Any]]:
    """Pull structured command info from terminal events."""
    commands = []
    for event in terminal_events:
        meta = _parse_metadata(event.get("metadata"))
        cmd = meta.get("command", "")
        if not cmd and event.get("event_type") == "terminal_spawned":
            cmd = "[terminal opened]"

        commands.append({
            "command": cmd,
            "timestamp": event.get("timestamp", ""),
            "category": _categorize_command(cmd),
            "exitCode": meta.get("exitCode"),
            "output": (meta.get("output", "") or "")[:500],  # cap output
        })

    return sorted(commands, key=lambda c: c.get("timestamp", ""))


def _categorize_command(cmd: str) -> str:
    """Categorize a shell command."""
    cmd_lower = cmd.lower().strip()

    if not cmd_lower or cmd_lower == "[terminal opened]":
        return "terminal_open"
    if any(t in cmd_lower for t in ["npm test", "npm run test", "vitest", "jest", "pytest", "npx vitest"]):
        return "test_run"
    if any(t in cmd_lower for t in ["npm run dev", "npm start", "node ", "python "]):
        return "dev_server"
    if any(t in cmd_lower for t in ["npm install", "npm i ", "yarn add", "pip install"]):
        return "package_install"
    if any(t in cmd_lower for t in ["npm run lint", "eslint", "prettier"]):
        return "lint"
    if any(t in cmd_lower for t in ["npm run build", "tsc", "webpack"]):
        return "build"
    if any(t in cmd_lower for t in ["git ", "cat ", "ls ", "grep ", "find "]):
        return "exploration"
    if any(t in cmd_lower for t in ["curl", "wget", "http"]):
        return "api_test"
    return "other"


# ─── Test behavior ─────────────────────────────────────────────────────────────

def _analyze_test_behavior(
    commands: List[Dict],
    all_interactions: List[Dict],
) -> Dict[str, Any]:
    """
    How did the candidate use tests?
    - How many times ran tests?
    - Before or after code changes?
    - Did test results improve over time?
    """
    test_runs = [c for c in commands if c["category"] == "test_run"]

    if not test_runs:
        return {
            "totalTestRuns": 0,
            "ranTestsBeforeFixing": False,
            "ranTestsAfterFixing": False,
            "testRunTimeline": [],
            "assessment": "never_tested",
        }

    # Timeline of test runs
    test_timeline = []
    for run in test_runs:
        # Count code modifications before this test run
        mods_before = sum(
            1 for e in all_interactions
            if e.get("event_type") == "code_modified"
            and e.get("timestamp", "") < run["timestamp"]
        )
        test_timeline.append({
            "timestamp": run["timestamp"],
            "modsBeforeThis": mods_before,
            "output_snippet": run.get("output", "")[:200],
        })

    # Did they run tests FIRST (before any code change)?
    first_test_ts = test_runs[0]["timestamp"] if test_runs else ""
    first_code_change = None
    for e in all_interactions:
        if e.get("event_type") in ("code_modified", "code_pasted_from_ai"):
            first_code_change = e.get("timestamp", "")
            break

    ran_tests_first = bool(
        first_test_ts and first_code_change and first_test_ts < first_code_change
    )

    # Did they run tests AFTER making changes? (most recent test is after most recent change)
    last_code_change = None
    for e in reversed(all_interactions):
        if e.get("event_type") in ("code_modified", "code_pasted_from_ai"):
            last_code_change = e.get("timestamp", "")
            break

    ran_tests_after = bool(
        test_runs and last_code_change and test_runs[-1]["timestamp"] > last_code_change
    )

    # Determine testing pattern
    total_test_runs = len(test_runs)
    if total_test_runs == 0:
        assessment = "never_tested"
    elif total_test_runs == 1 and ran_tests_first:
        assessment = "baseline_only"  # ran tests once at start
    elif total_test_runs == 1:
        assessment = "single_check"  # ran once (probably at end)
    elif ran_tests_first and ran_tests_after and total_test_runs >= 3:
        assessment = "test_driven"  # excellent — tests before and after
    elif ran_tests_after and total_test_runs >= 2:
        assessment = "iterative_testing"  # good — tests after changes
    else:
        assessment = "occasional_testing"

    return {
        "totalTestRuns": total_test_runs,
        "ranTestsBeforeFixing": ran_tests_first,
        "ranTestsAfterFixing": ran_tests_after,
        "testRunTimeline": test_timeline[:10],
        "assessment": assessment,
    }


# ─── Dev server analysis ──────────────────────────────────────────────────────

def _analyze_dev_server(commands: List[Dict]) -> Dict[str, Any]:
    """Did they start the dev server?"""
    dev_cmds = [c for c in commands if c["category"] == "dev_server"]
    return {
        "started": len(dev_cmds) > 0,
        "startCount": len(dev_cmds),
    }


# ─── Package installs ─────────────────────────────────────────────────────────

def _analyze_package_installs(commands: List[Dict]) -> Dict[str, Any]:
    """Did they install additional packages? Which ones?"""
    install_cmds = [c for c in commands if c["category"] == "package_install"]
    packages = []
    for cmd_info in install_cmds:
        cmd = cmd_info["command"]
        # Try to extract package names
        parts = cmd.split()
        for i, part in enumerate(parts):
            if part in ("install", "add", "i") and i + 1 < len(parts):
                for pkg in parts[i + 1:]:
                    if not pkg.startswith("-"):
                        packages.append(pkg)

    return {
        "installCount": len(install_cmds),
        "packages": packages[:20],
    }


# ─── Debug commands ────────────────────────────────────────────────────────────

def _analyze_debug_commands(commands: List[Dict]) -> Dict[str, Any]:
    """Count exploration/debugging commands."""
    exploration = [c for c in commands if c["category"] == "exploration"]
    lint = [c for c in commands if c["category"] == "lint"]
    build = [c for c in commands if c["category"] == "build"]
    api_test = [c for c in commands if c["category"] == "api_test"]

    return {
        "explorationCommands": len(exploration),
        "lintRuns": len(lint),
        "buildRuns": len(build),
        "apiTests": len(api_test),
    }


# ─── Engagement score ─────────────────────────────────────────────────────────

def _compute_engagement(
    test_analysis: Dict,
    dev_server: Dict,
    debug_commands: Dict,
) -> Dict[str, Any]:
    """
    How engaged was the candidate with the development environment?
    Candidates who only paste AI code and never run/test/debug score low.
    """
    score = 20  # baseline

    # Test engagement
    test_assessment = test_analysis.get("assessment", "never_tested")
    test_scores = {
        "test_driven": 30,
        "iterative_testing": 25,
        "occasional_testing": 15,
        "single_check": 10,
        "baseline_only": 8,
        "never_tested": 0,
    }
    score += test_scores.get(test_assessment, 0)

    # Dev server
    if dev_server.get("started"):
        score += 10

    # Exploration
    if debug_commands.get("explorationCommands", 0) > 0:
        score += 10
    if debug_commands.get("lintRuns", 0) > 0:
        score += 10
    if debug_commands.get("buildRuns", 0) > 0:
        score += 5
    if debug_commands.get("apiTests", 0) > 0:
        score += 15

    assessment = (
        "highly_engaged" if score >= 70
        else "moderately_engaged" if score >= 40
        else "minimally_engaged" if score >= 20
        else "disengaged"
    )

    return {
        "score": min(100, score),
        "assessment": assessment,
    }


# ─── Helpers ───────────────────────────────────────────────────────────────────

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
        "totalCommands": 0,
        "commands": [],
        "testBehavior": {"totalTestRuns": 0, "assessment": "never_tested"},
        "devServer": {"started": False},
        "packageInstalls": {"installCount": 0},
        "debugCommands": {},
        "engagementScore": {"score": 0, "assessment": "disengaged"},
    }
