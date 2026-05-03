"""
Agent 5: WebContainer Structure Builder

Main orchestrator for fullstack assessment generation.
Calls llm_generator (Azure OpenAI gpt-4.1) as the primary and only builder.
Raises an error if generation fails — no silent fallbacks.
"""

import logging
from typing import Dict, List, Any, Optional

from llm_generator import generate_with_llm

logger = logging.getLogger(__name__)


def build_webcontainer_structure(
    tasks: List[Dict[str, Any]],
    problems: Dict[str, str],
    validated_deps: Dict[str, Any],
    tech_stack: List[str],
    language: str = "javascript",
    job_role: Optional[str] = None,
    experience_level: Optional[str] = None,
    skills_to_test: Optional[List[str]] = None,
    problem_types: Optional[List[str]] = None,
    complexity: str = "medium",
    company_name: Optional[str] = None,
    job_description: Optional[str] = None,
    variant_index: int = 0,
    total_variants: int = 1,
) -> Dict[str, Any]:
    """
    Main orchestrator for assessment generation.
    Calls Azure OpenAI via llm_generator to produce the full project file structure.
    Raises RuntimeError if generation fails.
    """
    logger.info(f"[Agent5] Starting generation for role={job_role}, stack={tech_stack}, complexity={complexity}")

    llm_result = generate_with_llm(
        job_role=job_role or "Full Stack Engineer",
        experience_level=experience_level or "Mid-level",
        tech_stack=tech_stack or [language],
        tasks=tasks or [],
        skills_to_test=skills_to_test or [],
        problem_types=problem_types or [],
        complexity=complexity or "medium",
        company_name=company_name or "",
        job_description=job_description or "",
        validated_deps=validated_deps or {},
        variant_index=variant_index,
        total_variants=total_variants,
    )

    file_structure = llm_result.get("fileStructure") or {}
    intentional_issues = llm_result.get("intentionalIssues") or []

    if not file_structure:
        raise RuntimeError(
            f"[Agent5] LLM returned empty fileStructure for role={job_role}. "
            "Check OpenAI API key, model, and prompt."
        )

    runtime = "node" if any(
        str(t).lower() in ["react", "javascript", "typescript"]
        for t in (tech_stack or [])
    ) else "browser"

    logger.info(f"[Agent5] Generation complete — {len(file_structure)} files, {len(intentional_issues)} intentional issues")

    # Try to extract actual deps from the generated package.json (most accurate)
    generated_deps = {}
    generated_dev_deps = {}
    pkg_json_content = file_structure.get("frontend/package.json", "")
    if pkg_json_content:
        try:
            import json as _json
            pkg = _json.loads(pkg_json_content)
            generated_deps = pkg.get("dependencies", {})
            generated_dev_deps = pkg.get("devDependencies", {})
        except Exception:
            pass

    # Fall back to validated_deps from Agent 3 if package.json wasn't parseable
    deps_to_return = generated_deps or validated_deps or {}

    return {
        "name": f"assessment-{language}",
        "runtime": runtime,
        "packageManager": "npm",
        "dependencies": deps_to_return,
        "devDependencies": generated_dev_deps,
        "scripts": {},
        "fileStructure": file_structure,
        "intentionalIssues": intentional_issues,
    }



