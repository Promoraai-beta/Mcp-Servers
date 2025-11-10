"""
MCP Tool Handlers for Server B
Contains the actual tool execution logic
"""

import json
import logging
from typing import Any, Dict, List

from mcp.types import TextContent

from agents.agent_3_validator import validate_dependencies
from agents.agent_4_leetcode_generator import generate_leetcode_problems
import os
from agents.agent_5_builder import build_webcontainer_structure
from llm_generator import generate_with_llm

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
    
    logger.info(f"Building WebContainer structure for {job_role or 'generic'} project")

    # Per-request LLM overrides
    arg_use_llm = arguments.get("useLLM")
    env_use_llm = os.environ.get("USE_LLM", "false").lower() == "true"
    use_llm = arg_use_llm if isinstance(arg_use_llm, bool) else env_use_llm
    llm_model = arguments.get("llmModel") or os.environ.get("OPENAI_MODEL")
    file_structure = {}
    if use_llm:
        logger.info("USE_LLM=true → attempting LLM project generation")
        try:
            file_structure = generate_with_llm(
                job_role=job_role or "Frontend Developer",
                experience_level=experience_level or "Mid-level",
                tech_stack=tech_stack or [language],
                tasks=tasks or [],
                skills_to_test=skills_to_test or [],
                problem_types=problem_types or [],
                complexity=complexity or "medium",
                model=llm_model,
            )
            # Sanitize common issues from LLM output
            file_structure = _sanitize_llm_file_structure(file_structure, tech_stack)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            file_structure = {}

    # If LLM failed or disabled, fall back to deterministic builder
    if not file_structure:
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
            complexity=complexity
        )
    else:
        # Wrap LLM files into a template spec shape compatible with backend
        # Choose defaults for runtime/package manager based on language/stack
        runtime = "node" if any(t for t in (tech_stack or []) if str(t).lower() in ["react", "javascript", "typescript"]) else "browser"
        package_manager = "npm" if runtime == "node" else "npm"
        result = {
            "name": f"assessment-{language}",
            "runtime": runtime,
            "packageManager": package_manager,
            "dependencies": {},
            "devDependencies": {},
            "scripts": {},
            "fileStructure": file_structure,
        }
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


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
            json.loads(normalized["package.json"])  # fast path
        except Exception:
            # Try to interpret as Python-like dict and convert to strict JSON
            try:
                import ast
                py_obj = ast.literal_eval(normalized["package.json"])  # may raise
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


# Tool handler mapping
TOOL_HANDLERS = {
    "validate_dependencies": handle_validate_dependencies,
    "generate_leetcode_problems": handle_generate_leetcode_problems,
    "build_webcontainer_structure": handle_build_webcontainer_structure
}

