"""
OpenAI Agents SDK orchestration for Server B.

Architecture
─────────────────────────────────────────────────────────────
Single invite  →  run_single_variant()
  └── 1 TemplateBuilderAgent  (fresh unique template per candidate)

Bulk invite (N candidates, max 10 unique variants)
  └── run_bulk_variants()
        ├── asyncio.Semaphore(MAX_PARALLEL) caps concurrency
        └── min(N, 10) TemplateBuilderAgents run in parallel
            each gets a distinct scenario from VARIANT_CATALOGUE

Fallback: if openai-agents is not installed, falls through to
the legacy direct-LLM path in llm_generator.py so nothing breaks.
─────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

# ── .env loading ──────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=_env if _env.exists() else None, override=True)
except ImportError:
    pass

logger = logging.getLogger(__name__)

# ── SDK availability guard ────────────────────────────────────────────────────
try:
    from openai import AsyncAzureOpenAI, AsyncOpenAI
    from agents import Agent, Runner, ModelSettings
    from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
    # Disable tracing — suppress any initialisation errors (e.g. missing SOCKS deps in CI)
    try:
        from agents import set_tracing_disabled
        set_tracing_disabled(True)
    except Exception:
        pass
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False
    logger.warning("[Orchestrator] openai-agents not installed — using legacy llm_generator fallback")

# ── Local imports ─────────────────────────────────────────────────────────────
from llm_generator import (
    SYSTEM_PROMPT,
    _build_prompt,
    _validate_output,
    REACT_VITE_DEPS,
    AUTH_SCAFFOLD,
    ENV_TEMPLATE,
    INDEX_HTML_TEMPLATE,
    VITE_CONFIG_TEMPLATE,
    TSCONFIG_TEMPLATE,
    TSCONFIG_NODE_TEMPLATE,
    TEST_SETUP_TEMPLATE,
    BUG_TYPE_POOL,
    VARIANT_BUG_ASSIGNMENTS,
    assign_bug_types,
)

# Max simultaneous LLM agent pipelines — never more than this regardless of batch size
MAX_PARALLEL = 10


# ── Azure / OpenAI async client ───────────────────────────────────────────────
def _async_client_and_model() -> tuple[Any, str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    if azure_endpoint:
        client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        )
        return client, os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
    client = AsyncOpenAI(api_key=api_key)
    return client, os.environ.get("OPENAI_MODEL", "gpt-4o")


def _make_agent(variant_index: int, total_variants: int) -> "Agent":
    """
    Build one TemplateBuilderAgent.
    Temperature is higher for multi-variant runs to force structural diversity.
    response_format is injected via extra_body (ModelSettings v0.15+ dropped the direct field).
    """
    client, deployment = _async_client_and_model()
    model = OpenAIChatCompletionsModel(model=deployment, openai_client=client)
    temperature = 1.1 if total_variants > 1 else 0.7

    return Agent(
        name=f"TemplateBuilderAgent-v{variant_index}",
        instructions=SYSTEM_PROMPT,
        model=model,
        model_settings=ModelSettings(
            temperature=temperature,
            max_tokens=32000,
            extra_body={"response_format": {"type": "json_object"}},
        ),
    )


# ── Post-processing (shared with legacy path) ─────────────────────────────────
def _post_process(raw_json: str, tech_stack: list[str]) -> dict:
    """
    Parse agent JSON output, inject pinned infra files, merge package.json deps,
    and validate structure. Returns {fileStructure, intentionalIssues, valid, validationErrors}.
    """
    data = json.loads(raw_json)
    if not isinstance(data, dict):
        raise ValueError("Agent returned non-dict JSON")

    if "fileStructure" in data and isinstance(data["fileStructure"], dict):
        file_structure: dict[str, str] = data["fileStructure"]
        intentional_issues: list = data.get("intentionalIssues") or []
    else:
        file_structure = {k: v for k, v in data.items() if k != "intentionalIssues"}
        intentional_issues = data.get("intentionalIssues") or []

    # Normalise values to strings
    file_structure = {
        str(k): (str(v) if not isinstance(v, str) else v)
        for k, v in file_structure.items()
    }

    has_frontend = any(k.startswith("frontend/") for k in file_structure)
    has_backend  = any(k.startswith("backend/")  for k in file_structure)

    if has_frontend:
        file_structure.setdefault("frontend/index.html",        INDEX_HTML_TEMPLATE)
        file_structure.setdefault("frontend/vite.config.ts",    VITE_CONFIG_TEMPLATE)
        file_structure.setdefault("frontend/tsconfig.json",     TSCONFIG_TEMPLATE)
        file_structure.setdefault("frontend/tsconfig.node.json",TSCONFIG_NODE_TEMPLATE)
        file_structure.setdefault("frontend/src/test/setup.ts", TEST_SETUP_TEMPLATE)

    file_structure.setdefault(".env", ENV_TEMPLATE)

    if has_backend:
        file_structure.setdefault("backend/auth.py",            AUTH_SCAFFOLD)
        file_structure.setdefault("backend/__init__.py",        "")
        file_structure.setdefault("backend/routes/__init__.py", "")

        pkg_key = "frontend/package.json"
        try:
            pkg = json.loads(file_structure.get(pkg_key, "{}"))
            pkg.setdefault("name", "frontend")
            pkg.setdefault("version", "1.0.0")
            pkg.setdefault("private", True)
            pkg.setdefault("type", "module")
            pkg.setdefault("scripts", {
                "dev": "vite", "build": "tsc && vite build",
                "preview": "vite preview", "test": "vitest run", "test:watch": "vitest",
            })
            pkg["dependencies"]    = {**pkg.get("dependencies", {}),    **REACT_VITE_DEPS["dependencies"]}
            pkg["devDependencies"] = {**pkg.get("devDependencies", {}), **REACT_VITE_DEPS["devDependencies"]}
            file_structure[pkg_key] = json.dumps(pkg, indent=2)
        except Exception as e:
            logger.warning(f"Could not merge frontend/package.json: {e}")

    errors = _validate_output(file_structure, intentional_issues)
    if errors:
        logger.warning(f"[Orchestrator] Validation: {len(errors)} errors — {errors[:3]}")

    return {
        "fileStructure":    file_structure,
        "intentionalIssues": intentional_issues,
        "valid":            len(errors) == 0,
        "validationErrors": errors,
    }


def get_variant_label(variant_index: int, assigned_bugs: list[dict]) -> str:
    """Return a short human-readable label describing this variant's bug assignment."""
    if not assigned_bugs:
        return f"variant-{variant_index}"
    return ", ".join(bt["id"] for bt in assigned_bugs[:2]) + (
        f" +{len(assigned_bugs) - 2} more" if len(assigned_bugs) > 2 else ""
    )


# ── Core runner ───────────────────────────────────────────────────────────────
async def _run_one(
    *,
    job_role: str,
    tech_stack: list[str],
    experience_level: str,
    complexity: str,
    company_name: str,
    job_description: str,
    tasks: list,
    validated_deps: dict,
    variant_index: int,
    total_variants: int,
    num_bugs: int,
    assigned_bugs: list[dict],
    semaphore: asyncio.Semaphore,
) -> dict:
    """Run one TemplateBuilderAgent under the shared semaphore."""
    async with semaphore:
        variant_label = get_variant_label(variant_index, assigned_bugs)
        logger.info(
            f"[Orchestrator] Starting agent variant={variant_index}/{total_variants} "
            f"num_bugs={num_bugs} bugs=[{variant_label}]"
        )

        prompt = _build_prompt(
            job_role=job_role,
            experience_level=experience_level,
            tech_stack=tech_stack,
            tasks=tasks,
            skills_to_test=[],
            problem_types=[],
            complexity=complexity,
            company_name=company_name,
            job_description=job_description,
            validated_deps=validated_deps,
            variant_index=variant_index,
            total_variants=total_variants,
            num_bugs=num_bugs,
            assigned_bugs=assigned_bugs,
        )

        agent = _make_agent(variant_index, total_variants)
        result = await Runner.run(agent, prompt)
        raw = result.final_output or "{}"

        parsed = _post_process(raw, tech_stack)
        file_count = len(parsed["fileStructure"])
        issue_count = len(parsed["intentionalIssues"])
        logger.info(
            f"[Orchestrator] Agent variant={variant_index} bugs=[{variant_label}] done — "
            f"{file_count} files, {issue_count} issues, valid={parsed['valid']}"
        )
        return {
            "variantIndex":  variant_index,
            "scenarioName":  variant_label,
            "fileCount":     file_count,
            "issueCount":    issue_count,
            **parsed,
        }


# ── Public API ────────────────────────────────────────────────────────────────
async def run_single_variant(
    job_role: str,
    tech_stack: list[str],
    experience_level: str = "Mid-level",
    complexity: str = "medium",
    company_name: str = "",
    job_description: str = "",
    tasks: list | None = None,
    validated_deps: dict | None = None,
    variant_index: int = 0,
    num_bugs: int = 3,
) -> dict:
    """
    Generate one fresh code template for a single candidate invite.
    total_variants=1 so the domain is inferred freely from job context.
    num_bugs controls exactly how many intentional issues are injected.
    Returns {variantIndex, fileStructure, intentionalIssues, valid}.
    """
    # Single invite — no pre-assigned bug types; LLM picks from task context
    assigned = assign_bug_types(0, 1, num_bugs)  # returns [] for total_variants=1

    if not AGENTS_SDK_AVAILABLE:
        from llm_generator import generate_with_llm
        result = generate_with_llm(
            job_role=job_role, experience_level=experience_level,
            tech_stack=tech_stack, tasks=tasks or [],
            complexity=complexity, company_name=company_name,
            job_description=job_description,
            validated_deps=validated_deps or {},
            variant_index=0, total_variants=1,
            num_bugs=num_bugs, assigned_bugs=assigned,
        )
        return {"variantIndex": 0, **result}

    sem = asyncio.Semaphore(1)
    return await _run_one(
        job_role=job_role, tech_stack=tech_stack,
        experience_level=experience_level, complexity=complexity,
        company_name=company_name, job_description=job_description,
        tasks=tasks or [], validated_deps=validated_deps or {},
        variant_index=variant_index, total_variants=1,
        num_bugs=num_bugs, assigned_bugs=assigned,
        semaphore=sem,
    )


async def run_bulk_variants(
    job_role: str,
    tech_stack: list[str],
    variant_count: int,
    experience_level: str = "Mid-level",
    complexity: str = "medium",
    company_name: str = "",
    job_description: str = "",
    tasks: list | None = None,
    validated_deps: dict | None = None,
    num_bugs: int = 3,
) -> list[dict]:
    """
    Generate up to MAX_PARALLEL unique templates for a bulk invite batch.
    Each variant gets a pre-computed, non-overlapping bug type assignment
    so candidates in the same batch cannot share answers.
    Caps at min(variant_count, MAX_PARALLEL) — 500 candidates still only
    triggers at most 10 parallel LLM calls.
    Returns list of {variantIndex, fileStructure, intentionalIssues, valid}.
    """
    actual_count = min(variant_count, MAX_PARALLEL)
    logger.info(
        f"[Orchestrator] Bulk run: requested={variant_count} actual={actual_count} "
        f"(cap={MAX_PARALLEL}) num_bugs={num_bugs}"
    )

    # Pre-compute bug assignments for all variants upfront so we can log the plan
    all_assignments = [
        assign_bug_types(i, actual_count, num_bugs)
        for i in range(actual_count)
    ]
    for i, bugs in enumerate(all_assignments):
        logger.info(
            f"[Orchestrator] Variant {i} bugs: {[b['id'] for b in bugs]}"
        )

    if not AGENTS_SDK_AVAILABLE:
        from llm_generator import generate_with_llm
        results = []
        for i in range(actual_count):
            r = generate_with_llm(
                job_role=job_role, experience_level=experience_level,
                tech_stack=tech_stack, tasks=tasks or [],
                complexity=complexity, company_name=company_name,
                job_description=job_description,
                validated_deps=validated_deps or {},
                variant_index=i, total_variants=actual_count,
                num_bugs=num_bugs, assigned_bugs=all_assignments[i],
            )
            results.append({"variantIndex": i, **r})
        return results

    sem = asyncio.Semaphore(MAX_PARALLEL)
    coros = [
        _run_one(
            job_role=job_role, tech_stack=tech_stack,
            experience_level=experience_level, complexity=complexity,
            company_name=company_name, job_description=job_description,
            tasks=tasks or [], validated_deps=validated_deps or {},
            variant_index=i, total_variants=actual_count,
            num_bugs=num_bugs, assigned_bugs=all_assignments[i],
            semaphore=sem,
        )
        for i in range(actual_count)
    ]

    results = await asyncio.gather(*coros, return_exceptions=True)

    output = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(f"[Orchestrator] Variant {i} failed: {r}")
        else:
            output.append(r)

    logger.info(f"[Orchestrator] Bulk done: {len(output)}/{actual_count} succeeded")
    return output
