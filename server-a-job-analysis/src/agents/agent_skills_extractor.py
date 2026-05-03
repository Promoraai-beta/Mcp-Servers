"""
Agent: Skills Extractor
Part of the Promora AI-powered hiring platform

Fast, focused LLM call: reads a job description and returns structured
skill extraction data that powers the Create Position modal.

Returns:
  skills            list[{name, category}]    — detected skills
  role              str                        — Frontend / Backend / Full-Stack / Data / General
  level             str                        — Junior / Mid / Senior / Staff / Intern
  ideLanguage       str                        — primary language for the IDE sandbox
  suggestedComponents list[str]               — recommended assessment component types
  suggestedNumTasks   int                     — recommended task count (1-10)
  suggestedBugTypes   list[str]               — bug categories to inject
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path if env_path.exists() else None, override=True)
except ImportError:
    pass

try:
    from openai import AzureOpenAI, OpenAI
except ImportError:
    AzureOpenAI = None
    OpenAI = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _make_client():
    """Return (client, model) preferring AzureOpenAI when configured."""
    api_key = os.environ.get("OPENAI_API_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    if azure_endpoint and AzureOpenAI is not None:
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        )
        model = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
        return client, model
    if OpenAI is not None:
        return OpenAI(api_key=api_key), os.environ.get("OPENAI_MODEL", "gpt-4o")
    return None, None


# ── System prompt ─────────────────────────────────────────────────────────────
_EXTRACT_SYSTEM_PROMPT = """You are a technical recruiter and engineering manager.
Given a job title and job description, extract structured information to configure a technical assessment.

Be precise and practical. Focus on what the candidate will actually need to demonstrate in a hands-on coding test."""

# ── JSON schema ───────────────────────────────────────────────────────────────
_EXTRACT_JSON_SCHEMA = {
    "name": "skills_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "skills": {
                "type": "array",
                "description": "All technical skills found in the job description",
                "items": {
                    "type": "object",
                    "properties": {
                        "name":     {"type": "string", "description": "Skill name, e.g. TypeScript"},
                        "category": {
                            "type": "string",
                            "enum": ["lang", "framework", "db", "cloud", "concept"],
                            "description": "lang=language, framework=library/framework, db=database, cloud=cloud/devops, concept=architecture/pattern",
                        },
                    },
                    "required": ["name", "category"],
                    "additionalProperties": False,
                },
                "minItems": 0,
                "maxItems": 30,
            },
            "role": {
                "type": "string",
                "enum": ["Frontend", "Backend", "Full-Stack", "Data", "General"],
                "description": "Primary engineering discipline",
            },
            "level": {
                "type": "string",
                "enum": ["Intern", "Junior", "Mid", "Senior", "Staff"],
                "description": "Seniority level inferred from the JD",
            },
            "ideLanguage": {
                "type": "string",
                "description": "Primary programming language for the IDE sandbox task (e.g. typescript, python, go)",
            },
            "suggestedComponents": {
                "type": "array",
                "description": "Assessment component types to include based on the role and JD",
                "items": {
                    "type": "string",
                    "enum": ["ide_project", "leetcode", "database", "docs", "sheets"],
                },
                "minItems": 1,
                "maxItems": 5,
            },
            "suggestedNumTasks": {
                "type": "integer",
                "description": "Recommended number of assessment tasks. Junior=2-3, Mid=3-4, Senior=4-5, Staff=5+. Add 1 for each additional major skill area (DB, algorithms, etc.)",
                "minimum": 1,
                "maximum": 10,
            },
            "suggestedBugTypes": {
                "type": "array",
                "description": "Bug categories to inject into the code, selected based on what this role is expected to handle",
                "items": {
                    "type": "string",
                    "enum": [
                        "Logic Errors", "Edge Cases", "Off-by-one",
                        "Null Handling", "Race Conditions", "Security Flaws",
                        "Memory Leaks", "Type Errors", "API Errors", "Performance",
                    ],
                },
                "minItems": 2,
                "maxItems": 8,
            },
        },
        "required": [
            "skills", "role", "level", "ideLanguage",
            "suggestedComponents", "suggestedNumTasks", "suggestedBugTypes",
        ],
        "additionalProperties": False,
    },
}


def _build_extract_prompt(job_title: str, job_description: str) -> str:
    return f"""Job Title: {job_title}

Job Description:
{job_description[:4000]}

---
Extract all relevant technical skills from the job description.
Infer the primary engineering discipline (role) and seniority level.
Recommend the most appropriate assessment components and task count for this role.
Select bug categories that a candidate at this level should be expected to handle.
"""


def run_skills_extractor(job_title: str, job_description: str) -> Dict[str, Any]:
    """
    Extract skills and assessment configuration from a job description.

    Returns a dict with:
      skills, role, level, ideLanguage,
      suggestedComponents, suggestedNumTasks, suggestedBugTypes
    """
    client, model = _make_client()
    if not client:
        raise RuntimeError(
            "No LLM client available. Set AZURE_OPENAI_ENDPOINT + OPENAI_API_KEY "
            "(Azure) or OPENAI_API_KEY (standard OpenAI)."
        )

    logger.info(f"Skills extractor: '{job_title}' (model={model})")

    prompt = _build_extract_prompt(job_title, job_description)
    messages = [
        {"role": "system", "content": _EXTRACT_SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ]

    last_err: Optional[Exception] = None
    for attempt in range(1, 3):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,          # low temp — extraction should be deterministic
                response_format={
                    "type": "json_schema",
                    "json_schema": _EXTRACT_JSON_SCHEMA,
                },
                max_tokens=1500,
            )
            content = resp.choices[0].message.content or ""
            if not content:
                raise RuntimeError("LLM returned empty response")
            result = json.loads(content)
            logger.info(
                f"Skills extracted: {len(result.get('skills', []))} skills, "
                f"role={result.get('role')}, level={result.get('level')}, "
                f"suggestedNumTasks={result.get('suggestedNumTasks')}"
            )
            return result
        except Exception as e:
            last_err = e
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt == 1:
                messages.append({
                    "role": "user",
                    "content": f"Previous attempt failed: {e}. Please retry following the schema strictly.",
                })

    raise RuntimeError(
        f"Skills extraction failed after 2 attempts. Last error: {last_err}"
    ) from last_err
