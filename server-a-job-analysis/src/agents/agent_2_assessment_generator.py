"""
Agent 2: Assessment Generator
Part of the Promora AI-powered hiring platform

Analyses job data (role, stack, level, recruiter-selected components) and uses
an LLM to produce 2-3 specific, rubric-ready assessment tasks.

The tasks are then passed to llm_generator.py in Server B which generates
the actual project files, intentional bugs, and tests.
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


# ── System prompt ─────────────────────────────────────────────────────────────
_TASK_SYSTEM_PROMPT = """You are a senior engineering manager designing a technical assessment that will be given to a candidate interviewing at a specific company.

The assessment must feel like it comes from that company's REAL codebase — not a tutorial or generic exercise.
A candidate should look at this and think "this is exactly the kind of work I'd do here."

═══════════════════════════════════════════════
STEP 1: INFER THE PRODUCT DOMAIN
═══════════════════════════════════════════════
Before generating tasks, identify the company's product domain from the company name + job description.
Then invent a plausible feature or service within that product that the candidate will work on.

Domain examples:
  Payments/Fintech    → invoice processing, payout reconciliation, fraud detection queue, subscription billing
  E-commerce          → cart checkout flow, inventory sync, order fulfilment status, return/refund handling
  SaaS B2B            → team role management, usage-based billing, audit log, webhook delivery system
  Healthcare          → appointment booking, prescription tracker, patient intake form, lab result viewer
  Logistics/Supply    → shipment tracking, warehouse pick-list, carrier rate calculator, route optimizer
  HR/Recruiting       → candidate pipeline, interview scheduling, offer approval workflow, headcount tracker
  DevTools/Platform   → CI pipeline monitor, feature flag manager, deploy log viewer, alert routing
  Unknown/generic     → invent the most plausible product from the job description

═══════════════════════════════════════════════
STEP 2: GENERATE TASKS THAT FEEL REAL
═══════════════════════════════════════════════
Each task must:
- Reference a specific feature of the inferred product (not a generic "form" or "endpoint")
- Use real-sounding file/component/function names tied to that domain
- Describe what is broken in terms a developer at that company would understand
- Have acceptance criteria that reference the actual failing behaviour (not "test passes")

TASK TITLE RULES:
  BAD  → "Fix State Bug in User Form"
  BAD  → "Add REST Endpoint for Users"
  BAD  → "Optimize Slow Database Query"
  GOOD → "Fix Race Condition in Concurrent Booking Confirmation"
  GOOD → "Repair Missing DB Commit in Payout Batch Processor"
  GOOD → "Fix Stale Closure in Live Shipment Tracker Component"
  GOOD → "Resolve Off-by-One in Paginated Invoice Line Items"
  GOOD → "Fix Auth Bypass on Bulk Order Status Update Endpoint"

DESCRIPTION RULES:
- Name the specific component, file, or function that is broken
- Say what symptom the user sees (not "it doesn't work" — "the payout total shows $0 after approval")
- Mention the failing test by name if applicable

ACCEPTANCE CRITERIA RULES:
- Observable and specific: "POST /api/payouts/:id/approve returns 200 and persists the approved_at timestamp"
- Not: "the endpoint works correctly"
- Reference the domain: "the candidate pipeline board reflects status change within the same session"

═══════════════════════════════════════════════
COMPONENT TYPE DEFINITIONS
═══════════════════════════════════════════════
Each task must use exactly one component type. Here is what each means:

  ide_project  → A code task inside a real monorepo running in a container.
                 The candidate finds a specific broken feature and fixes it.
                 Must name the exact file/component/route, describe the bug symptom,
                 and reference a failing test by name.
                 Example: "Fix stale closure in InvoiceDetailsPanel that shows outdated payment status"

  leetcode     → An algorithmic coding problem. Domain context from the JD must be woven in.
                 Example: "Given a stream of shipment events, find the first carrier with 3+ consecutive delays"

  database     → A SQL schema or query task. Must use domain-specific table/column names.
                 Example: "Add an index to audit_events and rewrite the slow monthly billing summary query"

  docs         → A design document, RFC, or architecture decision record.
                 Must be specific to the inferred product domain.
                 Example: "Write a design doc for migrating the invoice delivery queue from polling to webhooks"

  sheets       → A spreadsheet or data analysis task.
                 Example: "Write formulas to compute monthly churn from a subscription export CSV"

  design       → A system design or architecture question.
                 Example: "Design the data model and API for a multi-tenant audit log system"

═══════════════════════════════════════════════
TASK COUNT — CRITICAL RULE
═══════════════════════════════════════════════
Generate EXACTLY one task per selected component type — no more, no less per type.
EXCEPTION: ide_project may appear 2-3 times if budget allows and seniority is mid/senior.

Examples:
  ["ide_project"]                       → 2 tasks (easy + hard ide_project). Always generate 2 for ide_project-only.
  ["ide_project", "docs"]               → 2 tasks: 1 ide_project + 1 docs
  ["ide_project", "leetcode"]           → 2 tasks: 1 ide_project + 1 leetcode
  ["ide_project", "database", "docs"]   → 3 tasks: 1 of each
  ["ide_project", "database"]           → 3 tasks: 2 ide_project (easy + hard) + 1 database

NEVER skip a selected component type.

DIFFICULTY SPREAD:
When generating multiple tasks, vary the difficulty so candidates who are fast get challenged
and candidates who are slower still complete something meaningful.
A good spread makes the assessment readable as a story — warm up, main challenge, stretch goal.
The specific difficulty of each task should fit the domain and seniority level, not follow
a fixed formula.

DOCS TASK RULE:
The docs task must ask for something a developer at that company would actually write —
not a generic essay. It should be tightly coupled to the product domain:
  GOOD → "Write a runbook for the payment webhook retry system — cover what happens when
          the idempotency key expires mid-retry and how the on-call engineer recovers."
  BAD  → A generic "explain how React state works" or restating the coding task
The docs task prompt should include a pre-seeded stub in the codebase (a .md file with
headings already written) so candidates understand the expected structure and depth.
The stub headings should be domain-specific, not generic ("## Failure Modes" not "## Section 2").

═══════════════════════════════════════════════
TIME CALIBRATION (be honest)
═══════════════════════════════════════════════
  easy   / 15 min = ~20 lines, obvious fix in 1 file
  easy   / 20 min = ~40 lines, 1-2 files
  medium / 20 min = ~60 lines, requires understanding the system
  medium / 25 min = ~100 lines, 2-3 files
  medium / 30 min = ~150 lines, 3-4 files
  hard   / 30 min = ~200 lines, architectural judgment required
  hard   / 40 min = multi-file refactor or non-obvious root cause

Scale difficulty to seniority: Junior = easy/medium, Mid = medium, Senior = medium/hard.
Total duration must NOT exceed the stated time budget.
"""

# ── JSON schema for structured outputs ────────────────────────────────────────
_TASK_JSON_SCHEMA = {
    "name": "assessment_tasks",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id":                 {"type": "string"},
                        "title":              {"type": "string"},
                        "duration":           {"type": "string"},
                        "difficulty":         {"type": "string", "enum": ["easy", "medium", "hard"]},
                        "component":          {"type": "string", "enum": ["ide_project", "leetcode", "database", "docs", "sheets", "design"]},
                        "description":        {"type": "string"},
                        "acceptanceCriteria": {"type": "array", "items": {"type": "string"}},
                        "skillsTested":       {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["id", "title", "duration", "difficulty", "component", "description", "acceptanceCriteria", "skillsTested"],
                    "additionalProperties": False,
                },
                "minItems": 1,
                "maxItems": 6,
            }
        },
        "required": ["tasks"],
        "additionalProperties": False,
    },
}


def _build_task_prompt(
    job_title: str,
    job_description: str,
    company: str,
    role: str,
    stack: List[str],
    level: str,
    components: List[str],
    time_budget_minutes: int,
    bug_types: Optional[List[str]] = None,
) -> str:
    stack_str  = ", ".join(stack) if stack else "not specified"
    per_task   = time_budget_minutes // max(len(components), 1)
    comp_lines = "\n".join(f"  task #{i+1}: component = \"{c}\"" for i, c in enumerate(components))

    bug_hint = ""
    if bug_types:
        bug_hint = f"\nBug categories the recruiter wants to test: {', '.join(bug_types)}.\n" \
                   "When writing ide_project task descriptions, the bugs to fix must draw from these categories.\n"

    return f"""Company: {company}
Job Title: {job_title}
Role: {role} | Level: {level}
Stack: {stack_str}
Total time budget: {time_budget_minutes} min (~{per_task} min per task)
{bug_hint}
Required tasks — generate EXACTLY one task per line, in this order:
{comp_lines}

Total: {len(components)} task(s). Do not add extras. Do not skip any type.

Job Description:
{job_description[:3000]}

─── YOUR TASK ────────────────────────────────────────────────
1. In 1 sentence, state what product this company builds (infer from company name + JD).

2. Invent a specific, partially-broken feature of that product. Use real domain names
   (e.g. "PayoutBatchProcessor", "ShipmentStatusWebhook", "CandidatePipelineBoard").

3. Generate exactly {len(components)} task(s), one per required component above:
   - Match the component type exactly as listed
   - Reference specific files, components, or routes by name
   - Describe the exact symptom the user sees when the bug/gap is present
   - Set duration honestly using the time calibration anchors
   - Write acceptance criteria that are observable and domain-specific
   - For ide_project tasks: the bugs introduced must align with the bug categories listed above

A candidate at {company} should read this and immediately feel like they are already at work.
"""


# ── LLM task generator ────────────────────────────────────────────────────────

def _generate_tasks_with_llm(
    job_title: str,
    job_description: str,
    company: str,
    role: str,
    stack: List[str],
    level: str,
    components: List[str],
    time_budget_minutes: int,
    bug_types: Optional[List[str]] = None,
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Use OpenAI structured outputs to generate assessment tasks.
    Retries once on failure before raising.
    """
    client, default_model = _make_client()
    if not client:
        raise RuntimeError(
            "No LLM client available. Set AZURE_OPENAI_ENDPOINT + OPENAI_API_KEY "
            "(Azure) or OPENAI_API_KEY (standard OpenAI)."
        )

    chosen_model = model or default_model
    prompt       = _build_task_prompt(
        job_title, job_description, company,
        role, stack, level, components, time_budget_minutes,
        bug_types=bug_types,
    )
    messages = [
        {"role": "system", "content": _TASK_SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ]

    def _call_and_parse(attempt: int) -> List[Dict[str, Any]]:
        """Single attempt: call API → parse → validate → return task list."""
        logger.info(f"LLM attempt {attempt} (model={chosen_model})")
        try:
            resp = client.chat.completions.create(
                model=chosen_model,
                messages=messages,
                temperature=0.7,
                response_format={
                    "type": "json_schema",
                    "json_schema": _TASK_JSON_SCHEMA,
                },
                max_tokens=3000,
            )
        except Exception as api_err:
            raise RuntimeError(f"OpenAI API error: {api_err}") from api_err

        content = resp.choices[0].message.content or ""
        if not content:
            raise RuntimeError("OpenAI returned an empty response")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as je:
            raise RuntimeError(f"Failed to parse LLM JSON: {je} | raw={content[:200]}") from je

        tasks = parsed.get("tasks", [])
        if not tasks:
            raise RuntimeError("LLM returned zero tasks")

        # Post-validation: reject tasks whose component isn't in the selected set
        allowed = set(components)
        filtered = [t for t in tasks if t.get("component") in allowed]
        if not filtered:
            raise RuntimeError(
                f"All generated tasks used disallowed components. "
                f"Selected: {components}. Got: {[t.get('component') for t in tasks]}"
            )

        # Post-validation: every selected component must have at least one task
        covered = {t.get("component") for t in filtered}
        missing = set(components) - covered
        if missing:
            raise RuntimeError(
                f"Generated tasks missing coverage for component(s): {missing}. "
                f"Selected: {components}. Got components: {list(covered)}"
            )

        # Post-validation: total duration must not wildly exceed budget
        total_min = 0
        for t in filtered:
            try:
                total_min += int(str(t.get("duration", "25")).split()[0])
            except (ValueError, IndexError):
                pass
        if total_min > time_budget_minutes * 1.5:
            raise RuntimeError(
                f"Generated tasks total {total_min} min, exceeds budget {time_budget_minutes} min × 1.5"
            )

        # Return at most len(components) tasks — we've already expanded the list
        # to match the recruiter's numTasks, so cap = len(components).
        max_tasks = len(components)
        logger.info(f"Attempt {attempt}: {len(filtered)} valid tasks, total ~{total_min} min")
        return filtered[:max_tasks]

    # Try once; on failure retry once with a note, then hard-fail
    last_err: Optional[Exception] = None
    for attempt in range(1, 3):  # attempts 1 and 2
        try:
            return _call_and_parse(attempt)
        except Exception as e:
            last_err = e
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt == 1:
                # Add a corrective hint before retry
                messages.append({"role": "user", "content": f"Previous attempt failed: {e}. Please try again, following the schema strictly."})

    raise RuntimeError(
        f"Could not generate assessment tasks after 2 attempts. Last error: {last_err}. "
        "Check OPENAI_API_KEY and model availability."
    ) from last_err


# ── Public entry point ────────────────────────────────────────────────────────

def run_agent_2(job_data: dict) -> dict:
    """
    Analyse job data and return LLM-generated assessment tasks + project metadata.

    job_data shape:
      jobTitle: str
      company: str (optional)
      jobDescription: str
      assessmentPreferences:
        components: list[str]   e.g. ["ide_project", "database", "docs"]
        ideLanguage: str        e.g. "typescript"
        timeLimitMinutes: int   total assessment time (default 60)
    """
    try:
        logger.info("Starting Agent 2: Assessment Generator")

        if not _is_valid_job_data(job_data):
            logger.warning("Invalid job data")
            return {"suggestedAssessments": []}

        job_title   = job_data.get("jobTitle", "")
        company     = job_data.get("company", "")
        job_desc    = job_data.get("jobDescription", "")

        role  = _parse_role(job_data)
        stack = _parse_stack(job_data)
        level = _parse_level(job_data)

        prefs        = job_data.get("assessmentPreferences") or {}
        components   = prefs.get("components") or ["ide_project", "docs"]
        ide_language = prefs.get("ideLanguage", "typescript")
        time_budget  = int(prefs.get("timeLimitMinutes", 60))
        num_tasks    = prefs.get("numTasks")
        bug_types    = prefs.get("bugTypes") or []
        recruiter_skills = prefs.get("skills") or []

        # Merge recruiter-selected skills into the auto-detected stack.
        # Recruiter selections win — put them first, then append any auto-detected
        # items not already present (case-insensitive dedup).
        if recruiter_skills:
            merged = list(recruiter_skills)
            lower_merged = {s.lower() for s in merged}
            for s in stack:
                if s.lower() not in lower_merged:
                    merged.append(s)
                    lower_merged.add(s.lower())
            stack = merged

        # Expand the component list to match numTasks if recruiter asked for more
        # tasks than there are unique component types. Extra tasks are always
        # ide_project (the most natural "extra challenge" type).
        if num_tasks and num_tasks > len(components):
            extra = num_tasks - len(components)
            components = components + ["ide_project"] * extra

        logger.info(
            f"role={role}, level={level}, stack={stack}, components={components}, "
            f"budget={time_budget}min, numTasks={num_tasks}, bugTypes={bug_types}"
        )

        # Always AI-generated — raises RuntimeError if LLM is unavailable
        tasks = _generate_tasks_with_llm(
            job_title=job_title,
            job_description=job_desc,
            company=company,
            role=role,
            stack=stack,
            level=level,
            components=components,
            time_budget_minutes=time_budget,
            bug_types=bug_types if bug_types else None,
        )

        template_spec = _generate_template_metadata(stack, components, ide_language)

        _ROLE_TO_ASSESSMENT_TYPE = {
            "Frontend":   "frontend_fluency",
            "Backend":    "backend_fluency",
            "Data":       "analyst_fluency",
            "Full-Stack": "generic",
            "General":    "generic",
        }

        result = {
            "suggestedAssessments": tasks,
            "role":           role,
            "stack":          stack,
            "level":          level,
            "components":     components,
            "ideLanguage":    ide_language,
            "timeBudget":     time_budget,
            "numTasks":       len(tasks),
            "bugTypes":       bug_types,
            "templateSpec":   template_spec,
            "assessmentType": _ROLE_TO_ASSESSMENT_TYPE.get(role, "generic"),
        }
        logger.info(f"Agent 2 complete — {len(tasks)} tasks generated")
        return result

    except Exception as e:
        logger.error(f"Error in Agent 2: {e}")
        return {"suggestedAssessments": []}


# ── Validation ────────────────────────────────────────────────────────────────

def _is_valid_job_data(job_data: dict) -> bool:
    if not isinstance(job_data, dict):
        return False
    # company is optional; jobTitle + jobDescription required
    return bool(job_data.get("jobTitle")) and bool(job_data.get("jobDescription"))


# ── Parsers — produce signals fed to the LLM prompt ──────────────────────────

def _parse_role(job_data: dict) -> str:
    title = job_data.get("jobTitle", "").lower()
    desc  = job_data.get("jobDescription", "").lower()

    if any(k in title for k in ("frontend", "front-end", "front end", "ui developer", "ui engineer")):
        return "Frontend"
    if any(k in title for k in ("backend", "back-end", "back end", "server", "api engineer")):
        return "Backend"
    if any(k in title for k in ("data", "machine learning", "ml engineer", "ai engineer", "analyst", "scientist")):
        return "Data"
    if any(k in title for k in ("full-stack", "fullstack", "full stack")):
        return "Full-Stack"
    if any(k in desc for k in ("frontend", "front-end", "react", "vue", "angular")):
        return "Frontend"
    if any(k in desc for k in ("backend", "back-end", "api development", "server-side", "django", "flask", "express")):
        return "Backend"
    if any(k in desc for k in ("machine learning", "data pipeline", "analytics", "pandas", "spark")):
        return "Data"
    if any(k in desc for k in ("full-stack", "fullstack", "full stack")):
        return "Full-Stack"
    return "General"


def _parse_stack(job_data: dict) -> List[str]:
    text  = job_data.get("jobDescription", "").lower()
    stack = []
    checks = [
        ("Python",     ["python"]),
        ("JavaScript", ["javascript"]),
        ("TypeScript", ["typescript"]),
        ("Java",       ["java "]),
        ("Go",         [" golang", " go "]),
        ("Rust",       ["rust"]),
        ("Ruby",       ["ruby"]),
        ("React",      ["react"]),
        ("Vue",        ["vue"]),
        ("Angular",    ["angular"]),
        ("Django",     ["django"]),
        ("Flask",      ["flask"]),
        ("FastAPI",    ["fastapi"]),
        ("Express",    ["express"]),
        ("Spring",     ["spring"]),
        ("PostgreSQL", ["postgresql", "postgres"]),
        ("MySQL",      ["mysql"]),
        ("MongoDB",    ["mongodb", "mongo"]),
        ("Redis",      ["redis"]),
        ("SQLite",     ["sqlite"]),
        ("AWS",        ["aws"]),
        ("Azure",      ["azure"]),
        ("Docker",     ["docker"]),
        ("Kubernetes", ["kubernetes", "k8s"]),
    ]
    for name, keywords in checks:
        if any(k in text for k in keywords):
            stack.append(name)
    return list(dict.fromkeys(stack))


def _parse_level(job_data: dict) -> str:
    text = f"{job_data.get('jobTitle','')} {job_data.get('jobDescription','')}".lower()
    if any(k in text for k in ("intern", "internship", "entry level", "entry-level")):
        return "Intern"
    if any(k in text for k in ("junior", "jr.", "0-2 years", "1-2 years")):
        return "Junior"
    if any(k in text for k in ("staff", "principal", "distinguished", "8+ years", "10+ years")):
        return "Staff"
    if any(k in text for k in ("senior", "lead", "sr.", "5+ years", "6+ years", "7+ years")):
        return "Senior"
    return "Mid"


# ── Template metadata ─────────────────────────────────────────────────────────

def _generate_template_metadata(
    stack: List[str],
    components: List[str],
    ide_language: str,
) -> Dict[str, Any]:
    """
    Return lightweight project metadata for Server B.
    File generation is done by llm_generator.py.
    """
    has_python = any(t in stack for t in ("Python", "Django", "Flask", "FastAPI"))
    has_java   = "Java" in stack
    has_go     = "Go" in stack

    if "ide_project" in components or "database" in components:
        if has_python:
            runtime, pkg_mgr = "python:3.11-slim", "pip"
        elif has_java:
            runtime, pkg_mgr = "openjdk:17-jdk-slim", "maven"
        elif has_go:
            runtime, pkg_mgr = "golang:1.21-alpine", "go"
        else:
            runtime, pkg_mgr = "node:20-alpine", "npm"
    else:
        # LeetCode / docs — browser-based, no container needed
        runtime, pkg_mgr = "browser", "npm"

    return {
        "runtime":        runtime,
        "packageManager": pkg_mgr,
        "ideLanguage":    ide_language,
    }
