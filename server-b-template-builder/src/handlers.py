"""
MCP Tool Handlers for Server B
Contains the actual tool execution logic
"""

import json
import logging
import os
import asyncio
from typing import Any, Dict, List

from mcp.types import TextContent

from pipeline.agent_3_validator import validate_dependencies
from pipeline.agent_4_leetcode_generator import generate_leetcode_problems
from pipeline.agent_5_builder import build_webcontainer_structure

logger = logging.getLogger(__name__)


async def handle_validate_dependencies(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle validate_dependencies tool call."""
    deps = arguments.get("dependencies", {})
    tech_stack = arguments.get("techStack", [])
    package_manager = arguments.get("packageManager", "npm")
    
    logger.info(f"Validating dependencies for {package_manager}")
    result = validate_dependencies(deps, tech_stack, package_manager)
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_generate_leetcode_problems(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle generate_leetcode_problems tool call."""
    tasks = arguments.get("tasks", [])
    tech_stack = arguments.get("techStack", [])
    language = arguments.get("language", "javascript")
    
    logger.info(f"Generating LeetCode problems for {language}")
    result = generate_leetcode_problems(tasks, tech_stack, language)
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_build_webcontainer_structure(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle build_webcontainer_structure tool call."""
    tasks = arguments.get("tasks", [])
    problems = arguments.get("problems", {})
    validated_deps = arguments.get("validatedDeps", {})
    tech_stack = arguments.get("techStack", [])
    language = arguments.get("language", "javascript")
    job_role = arguments.get("jobRole")
    experience_level = arguments.get("experienceLevel")
    skills_to_test = arguments.get("skillsToTest")
    problem_types = arguments.get("problemTypes")
    complexity = arguments.get("complexity", "medium")
    company_name = arguments.get("companyName", "")
    job_description = arguments.get("jobDescription", "")
    variant_index = int(arguments.get("variantIndex", 0))
    total_variants = int(arguments.get("totalVariants", 1))

    logger.info(f"Building WebContainer structure for {job_role or 'generic'} project (company: {company_name or 'unknown'}) [variant {variant_index + 1}/{total_variants}]")

    result = build_webcontainer_structure(
        tasks=tasks,
        problems=problems,
        validated_deps=validated_deps,
        tech_stack=tech_stack,
        language=language,
        job_role=job_role,
        experience_level=experience_level,
        skills_to_test=skills_to_test,
        problem_types=problem_types,
        complexity=complexity,
        company_name=company_name,
        job_description=job_description,
        variant_index=variant_index,
        total_variants=total_variants,
    )

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


# Deprecated npm packages that no longer exist - map to their replacements
_DEPRECATED_NPM_PACKAGES = {
    "babel-core": "@babel/core",  # babel-core was deprecated in Babel 7
    "babel-preset-env": "@babel/preset-env",
    "babel-preset-react": "@babel/preset-react",
}


def _sanitize_deprecated_packages(pkg: Dict[str, Any]) -> Dict[str, Any]:
    """Replace deprecated npm packages with their modern equivalents."""
    for dep_key in ("dependencies", "devDependencies"):
        if dep_key not in pkg or not isinstance(pkg[dep_key], dict):
            continue
        deps = pkg[dep_key]
        for old_name, new_name in _DEPRECATED_NPM_PACKAGES.items():
            if old_name in deps:
                version = deps.pop(old_name)
                deps[new_name] = version
                logger.info(f"Replaced deprecated {old_name} with {new_name}")
    return pkg


def _sanitize_llm_file_structure(file_structure: Dict[str, str], tech_stack: List[str]) -> Dict[str, str]:
    """Ensure LLM outputs contain valid JSON for package.json and minimal runnable scripts.
    Falls back to a safe package.json if invalid.
    """
    if not isinstance(file_structure, dict):
        return {}

    # Normalize values to strings
    normalized: Dict[str, str] = {}
    for k, v in file_structure.items():
        try:
            normalized[str(k)] = v if isinstance(v, str) else json.dumps(v)
        except Exception:
            continue

    # Validate package.json
    if "package.json" in normalized:
        try:
            # must be valid JSON – if not, try Python-literal to JSON upgrade
            pkg = json.loads(normalized["package.json"])
            pkg = _sanitize_deprecated_packages(pkg)
            normalized["package.json"] = json.dumps(pkg, indent=2)
        except json.JSONDecodeError:
            # Try to interpret as Python-like dict and convert to strict JSON
            try:
                import ast
                py_obj = ast.literal_eval(normalized["package.json"])  # may raise
                py_obj = _sanitize_deprecated_packages(py_obj)
                normalized["package.json"] = json.dumps(py_obj, indent=2)
            except Exception:
                # Fall back to minimal known-good package.json
                normalized["package.json"] = json.dumps(_make_minimal_package_json(tech_stack), indent=2)
    else:
        # add minimal package.json for JS stacks
        if any(t.lower() in ["react", "javascript", "typescript", "node.js", "node"] for t in tech_stack or []):
            normalized["package.json"] = json.dumps(_make_minimal_package_json(tech_stack), indent=2)

    return normalized


def _make_minimal_package_json(tech_stack: List[str]) -> Dict[str, Any]:
    is_react = any(t.lower() == "react" for t in tech_stack or [])
    pkg = {
        "name": "generated-project",
        "version": "1.0.0",
        "private": True,
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview",
            "test": "jest"
        },
        "dependencies": {},
        "devDependencies": {
            "vite": "^5.0.0",
            "jest": "^29.7.0"
        }
    }
    if is_react:
        pkg["dependencies"].update({
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        })
        pkg["devDependencies"]["@vitejs/plugin-react"] = "^4.2.0"
    return pkg


async def handle_orchestrate_single_variant(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle orchestrate_single_variant tool call.
    Runs one TemplateBuilderAgent (OpenAI Agents SDK) to generate a fresh
    unique code template for a single candidate invite.
    """
    from orchestrator import run_single_variant

    job_role        = arguments.get("jobRole", "Full Stack Engineer")
    tech_stack      = arguments.get("techStack", [])
    experience_level= arguments.get("experienceLevel", "Mid-level")
    complexity      = arguments.get("complexity", "medium")
    company_name    = arguments.get("companyName", "")
    job_description = arguments.get("jobDescription", "")
    tasks           = arguments.get("tasks", [])
    validated_deps  = arguments.get("validatedDeps", {})
    variant_index   = int(arguments.get("variantIndex", 0))
    num_bugs        = int(arguments.get("numBugs", 3))

    logger.info(f"[Handler] orchestrate_single_variant role={job_role} variant={variant_index} num_bugs={num_bugs}")

    result = await run_single_variant(
        job_role=job_role,
        tech_stack=tech_stack,
        experience_level=experience_level,
        complexity=complexity,
        company_name=company_name,
        job_description=job_description,
        tasks=tasks,
        validated_deps=validated_deps,
        variant_index=variant_index,
        num_bugs=num_bugs,
    )

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_orchestrate_bulk_variants(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle orchestrate_bulk_variants tool call.
    Runs up to 10 TemplateBuilderAgents in parallel (semaphore-capped) to generate
    N unique variants for a bulk invite. 500 candidates → still only ≤10 LLM calls.
    Each variant gets a distinct bug type assignment — same domain, different bugs.
    """
    from orchestrator import run_bulk_variants

    job_role        = arguments.get("jobRole", "Full Stack Engineer")
    tech_stack      = arguments.get("techStack", [])
    variant_count   = int(arguments.get("variantCount", 1))
    experience_level= arguments.get("experienceLevel", "Mid-level")
    complexity      = arguments.get("complexity", "medium")
    company_name    = arguments.get("companyName", "")
    job_description = arguments.get("jobDescription", "")
    tasks           = arguments.get("tasks", [])
    validated_deps  = arguments.get("validatedDeps", {})
    num_bugs        = int(arguments.get("numBugs", 3))

    logger.info(f"[Handler] orchestrate_bulk_variants role={job_role} count={variant_count} num_bugs={num_bugs}")

    results = await run_bulk_variants(
        job_role=job_role,
        tech_stack=tech_stack,
        variant_count=variant_count,
        experience_level=experience_level,
        complexity=complexity,
        company_name=company_name,
        job_description=job_description,
        tasks=tasks,
        validated_deps=validated_deps,
        num_bugs=num_bugs,
    )

    return [TextContent(type="text", text=json.dumps({"variants": results}, indent=2))]


# Tool handler mapping
TOOL_HANDLERS = {
    "validate_dependencies":          handle_validate_dependencies,
    "generate_leetcode_problems":     handle_generate_leetcode_problems,
    "build_webcontainer_structure":   handle_build_webcontainer_structure,
    "orchestrate_single_variant":     handle_orchestrate_single_variant,
    "orchestrate_bulk_variants":      handle_orchestrate_bulk_variants,
}

