# LLM-based project generator for Server B
# Produces a fileStructure (dict[path] = content) using OpenAI

import os
import json
import logging
from typing import Dict, List, Any, Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You generate full, runnable project file trees as a JSON object mapping file paths to file contents. "
    "Target realistic, minimal projects tailored to the role, tech stack and complexity. Inject intentional issues "
    "(bugs, performance bottlenecks, accessibility issues) and include a README with task instructions. "
    "Always ensure the project can run (package.json for JS; requirements.txt for Python) and include at least one test."
)


def _build_prompt(job_role: str, experience_level: str, tech_stack: List[str], tasks: List[Dict[str, Any]],
                  skills_to_test: List[str], problem_types: List[str], complexity: str) -> str:
    return (
        "Generate a project as a JSON mapping of file paths to file contents.\n"
        f"jobRole: {job_role}\n"
        f"experienceLevel: {experience_level}\n"
        f"techStack: {', '.join(tech_stack)}\n"
        f"skillsToTest: {', '.join(skills_to_test or [])}\n"
        f"problemTypes: {', '.join(problem_types or [])}\n"
        f"complexity: {complexity}\n"
        f"tasks: {json.dumps(tasks)[:2000]}\n\n"
        "Requirements:\n"
        "- Return ONLY a JSON object (no markdown), keys are file paths, values are full file contents.\n"
        "- Include runnable setup (package.json for JS with scripts: dev, test).\n"
        "- Inject 3-6 intentional issues (bugs/performance/accessibility).\n"
        "- Include tests (e.g., Jest for JS) and a README with the task.\n"
    )


def generate_with_llm(
    job_role: str,
    experience_level: str,
    tech_stack: List[str],
    tasks: List[Dict[str, Any]],
    skills_to_test: Optional[List[str]] = None,
    problem_types: Optional[List[str]] = None,
    complexity: str = "medium",
    model: Optional[str] = None,
) -> Dict[str, str]:
    """Generate project files using OpenAI; returns fileStructure dict. Safe fallback to empty on failure."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        logger.warning("LLM not available (missing OPENAI_API_KEY or openai package)")
        return {}

    try:
        client = OpenAI(api_key=api_key)
        prompt = _build_prompt(job_role, experience_level, tech_stack, tasks, skills_to_test or [], problem_types or [], complexity)

        resp = client.chat.completions.create(
            model=(model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        if not isinstance(data, dict):
            logger.error("LLM returned non-dict response; falling back")
            return {}
        # Normalize keys to strings
        file_structure: Dict[str, str] = {}
        for k, v in data.items():
            try:
                file_structure[str(k)] = str(v)
            except Exception:
                continue
        return file_structure
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return {}
