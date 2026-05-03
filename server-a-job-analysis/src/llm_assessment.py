import os
import json
import logging
from typing import Dict, List, Any
from pathlib import Path

# Load .env file for production
try:
    from dotenv import load_dotenv
    # Load .env from server directory (parent of src/)
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        # Try loading from current directory
        load_dotenv(override=True)
except ImportError:
    pass  # python-dotenv not installed, use system env vars

try:
    from openai import AzureOpenAI, OpenAI
except Exception:
    AzureOpenAI = None
    OpenAI = None

logger = logging.getLogger(__name__)


def _make_client():
    """Return (client, model) using AzureOpenAI if configured, else standard OpenAI."""
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

SYSTEM_PROMPT = """You are a senior engineering manager analyzing a job posting to design a technical assessment.

Your job is to:
1. Extract role, stack, and seniority from the posting.
2. Infer the company's product domain from the company name + job description.
3. Generate 2-3 assessment task IDEAS that feel like they come from that specific company's real codebase.

DOMAIN INFERENCE — do this first:
- Fintech/payments company → tasks around transaction flows, reconciliation, pricing logic
- E-commerce → tasks around cart state, order status, inventory syncing
- SaaS/B2B → tasks around team permissions, subscription state, audit trails
- Healthcare → tasks around appointment scheduling, patient data, compliance checks
- Logistics → tasks around shipment tracking, warehouse ops, route calculation
- Recruiting/HR tech → tasks around candidate pipeline, interview scheduling, offer management
- Unknown → invent the most plausible product from the job description

TASK QUALITY RULES:
- Title must name a specific feature of the inferred product. NOT "Fix State Bug" — YES "Fix Race Condition in Invoice Submission Flow"
- Description must say what is broken in that specific feature and why it matters to users
- Components must be concrete acceptance criteria tied to that domain (not generic CRUD)
- Duration: 15-40 min per task. Be honest — a 3-line fix is 15 min, not 30.

BAD examples (never generate these):
  "Fix State Bug in Task Form", "Add User Endpoint to REST API", "Optimize Slow Database Query"

GOOD examples:
  "Fix Double-Charge Bug in Subscription Upgrade Flow"
  "Repair Broken Shipment Status Webhook Handler"
  "Fix Stale Cache in Candidate Pipeline Board"
  "Implement Missing Pagination on Invoice Line Items"
  "Fix Race Condition in Concurrent Appointment Booking"
"""


def build_prompt(job_title: str, company: str, job_description: str) -> str:
    return (
        f"Company: {company}\n"
        f"Job Title: {job_title}\n"
        f"Job Description:\n{job_description}\n\n"
        "Step 1: In 1 sentence, infer what product/feature this company builds.\n"
        "Step 2: Generate 2-3 assessment tasks that test skills from this specific domain.\n\n"
        "Return ONLY a JSON object with fields: role, stack (array), level, suggestedAssessments (array).\n"
        "Each suggestedAssessments item: title, duration (int minutes), components (array of acceptance criteria), "
        "description (1 sentence — what is broken and what feature it affects), requirements (same as components).\n"
        "Task titles must name specific features from the inferred product — not generic patterns."
    )


def build_prompt(job_title: str, company: str, job_description: str) -> str:
    return (
        f"jobTitle: {job_title}\n"
        f"company: {company}\n"
        f"jobDescription: {job_description}\n\n"
        "Return ONLY a JSON object with fields: role, stack (array), level, suggestedAssessments (array).\n"
        "Each suggestedAssessments item must have: title, duration (int), components (array), description (string), requirements (array).\n"
        "Tasks must be concrete and code-specific — describe real bugs to fix or real features to add."
    )


def generate_assessments_with_llm(job_title: str, company: str, job_description: str) -> Dict[str, Any]:
    client, model = _make_client()
    if not client:
        logger.warning("LLM not available (missing OPENAI_API_KEY or openai package)")
        return {}
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(job_title, company, job_description)}
            ],
            temperature=0.7,
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
