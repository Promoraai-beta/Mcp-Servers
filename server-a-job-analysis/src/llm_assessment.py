import os
import json
import logging
from typing import Dict, List, Any

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You extract job analysis and produce a compact JSON object with: role, stack, level, and suggestedAssessments.\n"
    "- role: one of Frontend, Backend, Full-Stack, Data\n"
    "- stack: array of technologies inferred (e.g., React, TypeScript, Node.js)\n"
    "- level: one of Junior, Mid-level, Senior\n"
    "- suggestedAssessments: 2-3 items with title, duration, components (array of strings)\n"
)


def build_prompt(job_title: str, company: str, job_description: str) -> str:
    return (
        f"jobTitle: {job_title}\n"
        f"company: {company}\n"
        f"jobDescription: {job_description}\n\n"
        "Return ONLY a JSON object with fields: role, stack (array), level, suggestedAssessments (array)."
    )


def generate_assessments_with_llm(job_title: str, company: str, job_description: str) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        logger.warning("LLM not available (missing OPENAI_API_KEY or openai package)")
        return {}
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(job_title, company, job_description)}
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        # Minimal shape validation
        if not isinstance(data, dict) or "suggestedAssessments" not in data:
            return {}
        # Normalize keys
        result = {
            "role": data.get("role"),
            "stack": data.get("stack") or [],
            "level": data.get("level"),
            "suggestedAssessments": data.get("suggestedAssessments") or []
        }
        return result
    except Exception as e:
        logger.error(f"LLM assessment generation failed: {e}")
        return {}
