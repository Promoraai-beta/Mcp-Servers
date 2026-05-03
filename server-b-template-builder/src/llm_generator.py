# LLM-based project generator for Server B
# Produces a fileStructure (dict[path] = content) using OpenAI

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Load .env file for production
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        load_dotenv(override=True)
except ImportError:
    pass

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


# ── Version-pinned dependency sets ───────────────────────────────────────────
# Always use these exact compatible versions to prevent plugin/semver mismatches.
REACT_VITE_DEPS = {
    "dependencies": {
        "react": "^18.3.1",
        "react-dom": "^18.3.1",
        "react-router-dom": "^6.26.2",
        "axios": "^1.7.7",
        "@tanstack/react-query": "^5.59.0",
        "lucide-react": "^0.460.0",
        "clsx": "^2.1.1"
    },
    "devDependencies": {
        "vite": "^5.4.8",
        "@vitejs/plugin-react": "^4.3.2",
        "typescript": "^5.5.3",
        "@types/react": "^18.3.5",
        "@types/react-dom": "^18.3.0",
        "@types/react-router-dom": "^5.3.3",
        "@types/node": "^22.5.4",
        "vitest": "^2.1.1",
        "jsdom": "^25.0.1",
        "@testing-library/react": "^16.0.1",
        "@testing-library/jest-dom": "^6.5.0",
        "@testing-library/user-event": "^14.5.2"
    }
}

PYTHON_FLASK_DEPS = [
    "flask==3.0.3",
    "flask-cors==5.0.0",
    "flask-sqlalchemy==3.1.1",
    "sqlalchemy==2.0.35",
    "psycopg2-binary==2.9.9",
    "python-dotenv==1.0.1",
    "alembic==1.13.3",
    "marshmallow==3.22.0",
    "pytest==8.3.3",
    "pytest-flask==1.3.0"
]

VITE_CONFIG_TEMPLATE = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
'''

INDEX_HTML_TEMPLATE = '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Assessment App</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''

TSCONFIG_TEMPLATE = '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
'''

TSCONFIG_NODE_TEMPLATE = '''{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
'''

TEST_SETUP_TEMPLATE = '''import '@testing-library/jest-dom'
'''

# ── Pre-built auth scaffold (injected into every generated backend) ────────────
# Candidates never implement auth — it's pre-built infrastructure.
# One route will be missing the @require_auth decorator (intentional bug).
AUTH_SCAFFOLD = '''import os
import functools
from flask import request, jsonify, g

API_TOKEN = os.environ.get("API_TOKEN", "dev-token-change-in-prod")


def require_auth(f):
    """Decorator: validates Bearer token from Authorization header."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        if not token or token != API_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated
'''

# ── Pre-built .env template (injected into every generated project) ────────────
ENV_TEMPLATE = '''DATABASE_URL=postgresql://postgres:postgres@localhost:5432/assessmentdb
API_TOKEN=dev-token-change-in-prod
FLASK_ENV=development
PORT=5000
'''

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a senior engineer at a real software company generating a realistic, partially-built codebase for a technical assessment.

Your output is a JSON object with exactly TWO top-level keys:
  "fileStructure": { "path/to/file": "full file content", ... }
  "intentionalIssues": [ { ... }, ... ]

═══════════════════════════════════════════════════════════════
PRODUCT REALISM — THIS IS THE MOST IMPORTANT SECTION
═══════════════════════════════════════════════════════════════

The codebase must feel like a REAL product at a REAL company — not a tutorial project.

1. INFER A PRODUCT DOMAIN from the company name and job description.
   - Fintech company → generate an invoicing dashboard, payment reconciliation flow, or transaction ledger
   - E-commerce → generate an order management system, inventory tracker, or fulfilment queue
   - SaaS B2B → generate a team settings panel, subscription billing flow, or audit log viewer
   - Healthcare → generate an appointment scheduler, patient record viewer, or prescription tracker
   - Logistics → generate a shipment tracker, warehouse inventory, or route optimizer
   - Unknown/generic → invent a plausible SaaS product (e.g. a project management tool, a CRM, a support ticket system)

2. USE DOMAIN-SPECIFIC NAMES throughout:
   - Components: NOT "UserForm" → USE "InvoiceLineItemEditor", "ShipmentStatusBadge", "SubscriptionPlanCard"
   - API routes: NOT "/api/users" → USE "/api/invoices/:id/line-items", "/api/shipments/bulk-update"
   - Models: NOT "Item" → USE "Invoice", "LineItem", "Shipment", "Subscription", "AuditEvent"
   - Variables: NOT "data", "item", "result" → USE "invoiceTotal", "shipmentManifest", "planTier"

3. GENERATE A RICH CODEBASE — more files = more realistic. You are NOT limited to the minimum.
   Aim for at least 15-25 files. Good examples of what to add beyond the minimum:
   - frontend/src/components/  → 2-4 domain-specific React components
   - frontend/src/hooks/       → 1-2 custom hooks (e.g. useInvoices, useShipmentStatus)
   - frontend/src/types/       → TypeScript interfaces for all domain models
   - frontend/src/api/         → API client module (axios wrapper with typed responses)
   - frontend/src/utils/       → domain-specific helpers (formatCurrency, parseShipmentDate)
   - backend/routes/           → separate route files per domain (invoices.py, shipments.py)
   - backend/services/         → business logic layer (invoice_service.py, email_service.py)
   - backend/schemas.py        → marshmallow or plain dict schemas for validation

4. THE CODE MUST BE PARTIALLY WORKING. Most features should work correctly.
   Only the specific intentional bugs should be broken. Everything else should be solid,
   production-quality code that a senior engineer would be proud of.

5. COMPONENT DEPTH: React components should have real state, real side effects, real error handling.
   Not just a form with one field. A real component has: loading states, error states, empty states,
   pagination or filtering, proper TypeScript types, and at least one non-trivial interaction.

6. UI VISUAL QUALITY — RAISE THE BAR:
   The UI must look like a real internal tool — not a tutorial project.
   Tailwind CSS via CDN is available in frontend/index.html and should be used, but the
   specific design choices (layout, color palette, component structure) should fit the domain.
   A fintech tool should feel different from a logistics dashboard.

   Standards to meet — HOW you meet them is up to you:
   - Status/state values must be visually distinct (colored, badged, or iconified) — not raw text
   - Loading states must be non-trivial (skeleton screens, spinners with context) — not "Loading..."
   - Error states must be actionable (explain what failed, offer retry) — not "Error: ..."
   - User actions (PATCH/DELETE/submit) must give visible feedback — not silent
   - Layout must have a clear hierarchy — header, nav, content, actions — not a wall of elements

   The component that renders status/state is a good intentional-bug location
   (e.g. wrong color for a specific state, wrong label mapping, off-by-one in a badge count).

7. BACKEND QUALITY STANDARDS:
   List endpoints on large collections should support pagination or filtering appropriate to the domain.
   Write endpoints should validate their inputs and return domain-appropriate error messages.
   Flask error handlers (404, 500) should return JSON, not HTML.
   The backend should feel like it was written by a team, not a single developer in a hurry —
   consistent response shapes, consistent error format, middleware for cross-cutting concerns.

   What those cross-cutting concerns ARE is domain-driven:
   - A fintech app might log every write for audit compliance
   - A healthcare app might rate-limit sensitive endpoints
   - A logistics app might add request-id headers for tracing
   Choose what fits. Don't add audit logging to a logistics app just to tick a box.

8. DATABASE DEPTH:
   The schema should have at least one object beyond plain tables that a senior candidate would
   notice and engage with — a view, a computed column, a trigger, a partial index, a materialized
   view, or a meaningful constraint. What that object IS should emerge from the domain:
   - Billing app → a view computing outstanding balances per account
   - Logistics app → a partial index on shipments WHERE status = 'in_transit'
   - HR app → a check constraint ensuring offer_amount > 0

   At least one index that a candidate should add must be deliberately missing.
   The missing index should be on the column used in the most performance-sensitive query
   (the one a recruiter would naturally run first — list all, sort by date, filter by status).

9. INTENTIONAL BUGS MUST SPAN ALL LAYERS:
   Do not cluster all bugs in one file or one layer. Spread them so a candidate who only
   looks at the frontend never finds the backend bug, and vice versa.
   Aim for at least one bug touching each of: React component logic, Flask route logic, SQL/ORM layer.
   The specific bug types should fit the domain — don't force a stale closure into an app
   where the more realistic bug would be a missing DB commit or a race condition on a
   double-submit button.

═══════════════════════════════════════════════════════════════
HARD STRUCTURAL REQUIREMENTS (non-negotiable)
═══════════════════════════════════════════════════════════════

MONOREPO LAYOUT:
  README.md                    ← FIRST KEY in fileStructure
  frontend/
    index.html                 ← REQUIRED — exact template provided
    package.json               ← pinned deps provided — merge your extras in
    vite.config.ts             ← exact template provided — do not modify
    tsconfig.json              ← provided — do not modify
    tsconfig.node.json         ← provided — do not modify
    src/
      main.tsx                 ← ReactDOM.createRoot — do not modify
      App.tsx                  ← root router/layout — customise with real routes
      [add more files freely]
  backend/
    requirements.txt           ← pinned deps provided — add extras if needed
    app.py                     ← Flask factory (create_app) + db.create_all
    models.py                  ← SQLAlchemy models — at least 2 domain tables
    conftest.py                ← pytest: SQLite in-memory test DB
    [add routes/, services/ freely]

TECHNICAL RULES:
1. Zero syntax errors. Zero missing imports. Every import resolves.
2. No placeholder stubs — "# TODO", "pass", "raise NotImplementedError", "// ..." are forbidden.
   Write the complete implementation.
3. backend/app.py MUST end with the standard Flask entrypoint:
     if __name__ == '__main__':
         port = int(os.environ.get('PORT', 5000))
         app.run(host='0.0.0.0', port=port, debug=True)
4. Backend uses PostgreSQL via DATABASE_URL env var. Tests use SQLite in-memory via conftest.py.
5. Vite proxy forwards /api to http://localhost:5000.

═══════════════════════════════════════════════════════════════
INTENTIONAL BUGS — DESIGN PHILOSOPHY
═══════════════════════════════════════════════════════════════

Bugs must be subtle, domain-relevant, and REAL engineering mistakes — not toy errors.
Good bugs:
  - A React component that fetches data in a stale closure (captures initial state, misses updates)
  - A POST endpoint that doesn't commit the DB transaction (returns 201 but data never persists)
  - A pagination hook that off-by-ones the cursor (last item always missing)
  - A price calculation that loses cents due to integer division
  - A bulk update route missing an auth check (any user can update any record)
  - An N+1 query in a list endpoint (one DB call per item instead of a JOIN)
  - A React form with double-submit race condition (button not disabled during inflight request)

Bad bugs (do NOT use):
  - Missing semicolons or typos
  - Wrong variable name that would be caught by TypeScript immediately
  - A comment that says "// this is wrong"

Each bug must have a FAILING TEST before fix and a PASSING TEST after fix.

AI-RESISTANCE — every bug must pass this test:
If a candidate pastes just the buggy function into an AI chat and asks "what's wrong?",
the AI should either miss the bug, give a confident but wrong fix, or fix a symptom
while missing the root cause. Bugs that an AI spots immediately from the code alone
are too easy — use bugs that require running the code, understanding the domain,
or knowing what the data looks like at runtime:

  GOOD (AI-resistant):
  - Business logic wrong for a specific edge case (e.g. refund calculation ignores
    already_refunded amount — code looks correct, domain knowledge required)
  - Bug only appears with >50 items (URL length truncation, off-by-one in batch size)
  - Correct fix introduces a second bug (AI adds db.session.commit() inside a loop
    instead of after it — partially fixes, creates new problem)
  - Race condition only visible under concurrent requests
  - SQL query correct but missing index makes it time out at scale (EXPLAIN ANALYZE needed)

  BAD (AI spots instantly):
  - Wrong variable name visible in same function
  - Missing import that TypeScript flags immediately
  - Logic error with a comment above describing the correct behaviour

═══════════════════════════════════════════════════════════════
FRONTEND TEST RULES — VITEST ONLY (not Jest)
═══════════════════════════════════════════════════════════════

- NEVER use jest.mock / jest.fn / jest.spyOn — jest is undefined. Use vi.* from 'vitest'.
- Correct test header:
    import { describe, it, expect, vi, beforeEach } from 'vitest'
    import { render, screen, waitFor } from '@testing-library/react'
    import userEvent from '@testing-library/user-event'
    vi.mock('axios')
- Tests should be meaningful: simulate real user interactions, assert real DOM outcomes.

Each intentionalIssue MUST be a JSON object with ALL keys:
  "id"                    string  snake_case unique identifier
  "description"           string  what is wrong and why it matters (2-3 sentences)
  "file"                  string  relative path to the affected file
  "line_hint"             string  approximate line number or function name
  "task_id"               string  matching assessment task id
  "severity"              string  low | medium | high | critical
  "category"              string  api_design | data_layer | frontend_state | security | accessibility | performance | testing
  "expected_failing_test" string  path::test name that FAILS before fix, PASSES after

README.md must have: Assessment Tasks (with acceptance criteria), Getting Started (frontend + backend commands). Do NOT reveal intentional bugs in the README.

Return ONLY the JSON object. No prose, no markdown fences.
"""


# ── Post-generation validator ──────────────────────────────────────────────────
MANDATORY_FRONTEND_FILES = [
    "frontend/index.html",
    "frontend/src/main.tsx",
    "frontend/package.json",
    "frontend/vite.config.ts",
]
MANDATORY_BACKEND_FILES = [
    "backend/app.py",
    "backend/requirements.txt",
]
PLACEHOLDER_PATTERNS = [
    "# TODO", "# ...", "// ...", "raise NotImplementedError", "pass  # implement",
    "/* implement */", "// implement", "YOUR CODE HERE",
]

# Test files must not use Jest globals — the runner is Vitest (vi.mock / vi.fn)
JEST_IN_VITEST_PATTERNS = ["jest.mock(", "jest.fn(", "jest.spyOn(", "jest.clearAllMocks("]


def _validate_output(
    file_structure: Dict[str, str],
    intentional_issues: List[Dict[str, Any]],
) -> List[str]:
    """
    Fast structural validation of generated output.
    Returns a list of error strings; empty list = valid.
    """
    import ast as _ast
    errors: List[str] = []
    has_frontend = any(k.startswith("frontend/") for k in file_structure)
    has_backend = any(k.startswith("backend/") for k in file_structure)

    # 1. Mandatory file presence
    if has_frontend:
        for f in MANDATORY_FRONTEND_FILES:
            if f not in file_structure:
                errors.append(f"Missing mandatory file: {f}")
    if has_backend:
        for f in MANDATORY_BACKEND_FILES:
            if f not in file_structure:
                errors.append(f"Missing mandatory file: {f}")
    if "README.md" not in file_structure:
        errors.append("Missing README.md")

    # 2. package.json parseable JSON
    for path, content in file_structure.items():
        if path.endswith("package.json"):
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(f"{path}: invalid JSON — {e}")

    # 3. Python syntax check
    for path, content in file_structure.items():
        if path.endswith(".py"):
            try:
                _ast.parse(content)
            except SyntaxError as e:
                errors.append(f"{path}: Python syntax error at line {e.lineno} — {e.msg}")

    # 4. Placeholder stub detection
    for path, content in file_structure.items():
        for pat in PLACEHOLDER_PATTERNS:
            if pat in content:
                errors.append(f"{path}: contains placeholder stub '{pat}'")
                break

    # 5. Jest-in-Vitest detection — test files must use vi.* not jest.*
    for path, content in file_structure.items():
        if "__tests__" in path or path.endswith(".test.ts") or path.endswith(".test.tsx"):
            for pat in JEST_IN_VITEST_PATTERNS:
                if pat in content:
                    errors.append(
                        f"{path}: uses Jest API '{pat}' but runner is Vitest — use vi.{pat.split('.')[-1]} instead"
                    )
                    break

    # 6. intentionalIssues have required fields
    required_issue_fields = ("id", "description", "file", "severity", "category")
    for issue in intentional_issues:
        missing = [f for f in required_issue_fields if not issue.get(f)]
        if missing:
            errors.append(
                f"intentionalIssue '{issue.get('id', '?')}' missing fields: {missing}"
            )

    return errors


# ── Bug type pool ─────────────────────────────────────────────────────────────
# 12 named archetypes used to construct per-variant bug assignments.
# For single invites the LLM picks the most relevant types from this list
# based on the recruiter's tasks. For bulk invites each variant gets a
# pre-assigned non-overlapping slice so candidates can't share answers.
BUG_TYPE_POOL = [
    # 0
    {
        "id": "race_condition",
        "name": "Race Condition",
        "description": "Two concurrent requests claim or modify the same resource without a lock. "
                       "Example: a checkout button fires twice before the first request settles, "
                       "creating a duplicate order. Fix requires a DB-level lock, idempotency key, "
                       "or optimistic concurrency check.",
    },
    # 1
    {
        "id": "n_plus_one",
        "name": "N+1 Query",
        "description": "A list endpoint executes one extra DB query per row instead of a single JOIN "
                       "or eager-load. Invisible on small datasets; catastrophic at scale. "
                       "Fix: use SQLAlchemy joinedload / selectinload, or rewrite the query with a JOIN.",
    },
    # 2
    {
        "id": "missing_auth",
        "name": "Missing Auth Guard",
        "description": "One write or sensitive read route is missing the @require_auth decorator, "
                       "allowing any unauthenticated caller to invoke it. "
                       "Fix: add @require_auth above the route function.",
    },
    # 3
    {
        "id": "float_precision",
        "name": "Float Precision / Integer Division",
        "description": "A monetary amount, rate, or percentage is computed with float arithmetic or "
                       "integer division, producing silently wrong results (e.g. 10 / 3 = 3 in Python 2 style, "
                       "or 0.1 + 0.2 != 0.3). Fix: use Python Decimal / integer cents / explicit float().",
    },
    # 4
    {
        "id": "stale_closure",
        "name": "Stale Closure in React Hook",
        "description": "A useEffect, useCallback, or setInterval captures a value from an earlier render "
                       "and never sees updates. The component appears to work but shows stale data. "
                       "Fix: add the captured variable to the dependency array, or use a ref.",
    },
    # 5
    {
        "id": "pagination_off_by_one",
        "name": "Pagination Off-by-One",
        "description": "A cursor- or offset-based paginator skips or duplicates the boundary record. "
                       "The last item of page N is either missing or appears again as the first item of page N+1. "
                       "Fix: correct the < vs <= comparison or the OFFSET arithmetic.",
    },
    # 6
    {
        "id": "missing_db_commit",
        "name": "Missing DB Commit",
        "description": "A write route calls db.session.add() but never db.session.commit(). "
                       "The route returns 201 and the response looks correct, but the record "
                       "vanishes on server restart because it was never persisted. "
                       "Fix: add db.session.commit() after the add.",
    },
    # 7
    {
        "id": "wrong_sort_order",
        "name": "Wrong Sort / Status Mapping",
        "description": "A severity, priority, or status value is mapped in reverse "
                       "(e.g. HIGH severity sorts last, or 'in_transit' badge shows 'Delivered'). "
                       "The bug is in a lookup dict or sort comparator, not immediately obvious from code. "
                       "Fix: correct the mapping or flip the sort direction.",
    },
    # 8
    {
        "id": "missing_index",
        "name": "Missing Database Index",
        "description": "A high-cardinality column used in a WHERE or ORDER BY clause has no index. "
                       "Queries are fast on the seed dataset but time out in production. "
                       "Fix: add a CREATE INDEX (or SQLAlchemy Index()) on the relevant column. "
                       "Candidate must run EXPLAIN ANALYZE to discover it.",
    },
    # 9
    {
        "id": "double_submit",
        "name": "Double-Submit / Button Not Disabled",
        "description": "A form submit button is not disabled while the request is inflight, "
                       "letting a user click twice and create duplicate records. "
                       "Fix: set a loading/submitting state on click and disable the button until resolved.",
    },
    # 10
    {
        "id": "cache_invalidation",
        "name": "Stale Cache / Query Not Invalidated",
        "description": "After a mutation (create, update, delete) the UI continues to show the old data "
                       "because the React Query / SWR cache is never invalidated. "
                       "Fix: call queryClient.invalidateQueries() with the correct key after the mutation.",
    },
    # 11
    {
        "id": "silent_data_loss",
        "name": "Silent Data Loss on Partial Update",
        "description": "A PATCH handler uses model.__dict__.update(payload) or similar, "
                       "overwriting fields the caller did not intend to change (including setting them to null). "
                       "Fix: only update fields explicitly present in the request payload.",
    },
]

# ── Pre-computed variant bug assignments ──────────────────────────────────────
# 10 combinations of 4 bug types each, where any two variants share AT MOST 2
# types. This guarantees that even if a candidate describes a bug to another,
# the fix is always in a different feature area / different code context.
#
# Index references BUG_TYPE_POOL above:
#   0=race_condition  1=n_plus_one     2=missing_auth    3=float_precision
#   4=stale_closure   5=pagination     6=missing_commit  7=wrong_sort
#   8=missing_index   9=double_submit  10=cache_invalid  11=silent_data_loss
#
# Verified: no pair shares more than 2 elements.
VARIANT_BUG_ASSIGNMENTS = [
    [0, 1, 2, 3],    # V0: race, n+1, missing_auth, float
    [4, 5, 6, 7],    # V1: stale_closure, pagination, no_commit, wrong_sort
    [8, 9, 10, 11],  # V2: missing_index, double_submit, cache, silent_loss
    [0, 4, 9, 10],   # V3: race, stale_closure, double_submit, cache
    [1, 5, 8, 11],   # V4: n+1, pagination, missing_index, silent_loss
    [2, 6, 9, 11],   # V5: missing_auth, no_commit, double_submit, silent_loss
    [3, 7, 8, 10],   # V6: float, wrong_sort, missing_index, cache
    [0, 6, 8, 11],   # V7: race, no_commit, missing_index, silent_loss
    [1, 7, 9, 10],   # V8: n+1, wrong_sort, double_submit, cache
    [2, 4, 10, 11],  # V9: missing_auth, stale_closure, cache, silent_loss
]


def assign_bug_types(variant_index: int, total_variants: int, num_bugs: int) -> list[dict]:
    """
    Return the list of bug type dicts (from BUG_TYPE_POOL) assigned to this variant.

    Single invites (total_variants=1): returns empty list — the LLM picks the most
    relevant types from BUG_TYPE_POOL based on the recruiter's tasks.

    Bulk invites: returns a slice of the pre-computed VARIANT_BUG_ASSIGNMENTS for
    this variant index, extended if num_bugs > 4 by cycling through pool types not
    already assigned to this variant (lowest-reuse first).
    """
    if total_variants <= 1:
        return []  # Single invite — let the LLM decide from task context

    base_indices = VARIANT_BUG_ASSIGNMENTS[variant_index % len(VARIANT_BUG_ASSIGNMENTS)]

    if num_bugs <= len(base_indices):
        indices = base_indices[:num_bugs]
    else:
        # Need more types than the base assignment — supplement with remaining pool
        # types ordered by how infrequently they appear in other variants
        used_across = {i: 0 for i in range(len(BUG_TYPE_POOL))}
        for assignment in VARIANT_BUG_ASSIGNMENTS:
            for idx in assignment:
                used_across[idx] += 1

        remaining = [
            i for i in range(len(BUG_TYPE_POOL))
            if i not in base_indices
        ]
        # Sort by usage count (ascending) so we pick the least-reused types first
        remaining.sort(key=lambda i: used_across[i])
        extra_needed = num_bugs - len(base_indices)
        indices = base_indices + remaining[:extra_needed]

    return [BUG_TYPE_POOL[i] for i in indices]


def _build_variation_block(
    variant_index: int,
    total_variants: int,
    num_bugs: int,
    assigned_bugs: list[dict] | None = None,
) -> str:
    """
    Return a VARIATION DIRECTIVE block injected into the user prompt.

    Single invite  (total_variants=1): only enforces num_bugs count; domain and
    bug types are inferred by the LLM from company name + job description + tasks.

    Bulk invite (total_variants>1): locks the domain to the job description (NOT a
    hardcoded scenario catalogue), assigns specific bug archetypes per variant so
    no two candidates share the same set, and enforces num_bugs count.
    """
    if total_variants <= 1:
        # Single invite — just enforce the bug count
        return f"""
─── BUG COUNT REQUIREMENT ─────────────────────────────────────
Inject EXACTLY {num_bugs} intentional bug{'s' if num_bugs != 1 else ''} — no more, no fewer.
Choose the bug types that best match the recruiter's assessment tasks above.
Each bug must span a different layer (frontend / backend / database).
"""

    # Bulk invite — deterministic, non-overlapping bug assignment per variant
    bug_lines = "\n".join(
        f"  {i + 1}. [{bt['id']}] {bt['name']}: {bt['description']}"
        for i, bt in enumerate(assigned_bugs or [])
    )

    return f"""
═══════════════════════════════════════════════════════════════
VARIANT DIRECTIVE  (Variant {variant_index + 1} of {total_variants})
═══════════════════════════════════════════════════════════════

You are generating ONE of {total_variants} unique variants for the SAME job role and
company. ALL variants share the same product domain (inferred from the company name
and job description above) — do NOT invent a different industry or product.

Uniqueness comes from TWO things only:
  1. A DIFFERENT feature area within the same product (e.g. if the product is a
     fintech platform, one variant covers the reconciliation flow, another covers
     the invoice generation flow, another covers the audit trail — all fintech,
     all different code).
  2. A DIFFERENT set of intentional bugs (assigned below).

HARD CONSTRAINTS:
  - Domain MUST match the company/job description. Do NOT use e-commerce, healthcare,
    or logistics if the job description describes a fintech company.
  - File names, component names, route paths, and model names MUST reflect the
    actual product domain.
  - Do NOT use generic names: no "ItemList", no "/api/records", no "DataTable".
  - temperature=1.1 — lean into creative, domain-specific architectural decisions.

BUG COUNT: Inject EXACTLY {num_bugs} intentional bug{'s' if num_bugs != 1 else ''} — no more, no fewer.

ASSIGNED BUG TYPES FOR THIS VARIANT (implement all {len(assigned_bugs or [])} in domain-specific code):
{bug_lines}

These bug types are UNIQUE to this variant — other variants in this batch have
different assignments. A candidate who describes their bug to another candidate
will not be giving useful information because the feature area and code context differ.
"""


# ── User prompt builder ───────────────────────────────────────────────────────
def _build_prompt(
    job_role: str,
    experience_level: str,
    tech_stack: List[str],
    tasks: List[Dict[str, Any]],
    skills_to_test: List[str],
    problem_types: List[str],
    complexity: str,
    company_name: str = "",
    job_description: str = "",
    validated_deps: Optional[Dict[str, str]] = None,
    variant_index: int = 0,
    total_variants: int = 1,
    num_bugs: int = 3,
    assigned_bugs: Optional[List[Dict[str, Any]]] = None,
) -> str:
    has_python = any(t.lower() in ('python', 'fastapi', 'flask', 'django') for t in tech_stack)
    has_js = any(t.lower() in ('react', 'typescript', 'javascript', 'vue', 'next.js') for t in tech_stack)

    deps_block = ""
    if has_js:
        deps_block += (
            "\nUSE THESE EXACT frontend/package.json dependencies (do not change versions):\n"
            + json.dumps(REACT_VITE_DEPS, indent=2)
            + "\n\nUSE THIS EXACT frontend/vite.config.ts (do not modify):\n"
            + VITE_CONFIG_TEMPLATE
            + "\nUSE THIS EXACT frontend/index.html:\n"
            + INDEX_HTML_TEMPLATE
            + "\nUSE THIS EXACT frontend/tsconfig.json:\n"
            + TSCONFIG_TEMPLATE
            + "\nUSE THIS EXACT frontend/tsconfig.node.json:\n"
            + TSCONFIG_NODE_TEMPLATE
            + "\nUSE THIS EXACT frontend/src/test/setup.ts:\n"
            + TEST_SETUP_TEMPLATE
        )
    if has_python:
        deps_block += (
            "\nUSE THESE EXACT backend/requirements.txt lines (do not change versions):\n"
            + "\n".join(PYTHON_FLASK_DEPS)
        )

    # Inject Agent 3 validated deps as an additional seed hint
    if validated_deps:
        deps_block += (
            "\n\nADDITIONAL PRE-VALIDATED PACKAGES (Agent 3 confirmed these are safe to use — "
            "merge them into the relevant package.json dependencies, do not remove or downgrade):\n"
            + json.dumps(validated_deps, indent=2)
        )

    task_block = json.dumps(tasks, indent=2)[:4000]

    # Build company/domain context block — the richer this is, the more specific the output
    context_lines = []
    if company_name:
        context_lines.append(f"Company: {company_name}")
    if job_description:
        context_lines.append(f"Job context: {job_description[:1500]}")
    context_lines.append(f"Role: {job_role} ({experience_level})")
    context_lines.append(f"Tech stack: {', '.join(tech_stack)}")
    context_lines.append(f"Complexity: {complexity}")
    if skills_to_test:
        context_lines.append(f"Skills being tested: {', '.join(skills_to_test)}")
    context_block = "\n".join(context_lines)

    variation_block = _build_variation_block(
        variant_index, total_variants, num_bugs, assigned_bugs
    )

    return f"""Build a realistic, domain-specific assessment project for this engineering role.

─── CONTEXT ───────────────────────────────────────────────────
{context_block}
{variation_block}
─── ASSESSMENT TASKS (these drive the intentional bugs) ───────
{task_block}

─── WHAT TO BUILD ─────────────────────────────────────────────
1. Infer the company's product domain from the company name and job description.
   Invent a plausible, partially-built feature of that product. Name everything
   after the domain — components, routes, models, variables, file names.

2. The codebase should look like a real internal tool or product feature, NOT a tutorial.
   Minimum 15 files. Recommended: components/, hooks/, types/, api/, services/, routes/.

3. Inject EXACTLY {num_bugs} intentional bug{'s' if num_bugs != 1 else ''} — subtle, domain-relevant,
   requires real understanding to find. Each bug must have a failing test.
   Spread bugs across frontend, backend, and database layers.

4. Everything outside the intentional bugs must work correctly and look production-quality.

─── PINNED INFRASTRUCTURE (copy these exactly) ────────────────
{deps_block}

─── PRE-BUILT INFRASTRUCTURE (do NOT re-implement these) ──────
The following files are already injected into every project automatically.
Reference them in your generated code but do not redefine them:

  backend/auth.py      → exports require_auth decorator (Bearer token check)
                         Usage: from auth import require_auth
                         @require_auth on protected routes
                         LEAVE ONE route without @require_auth — this is an intentional security bug
  .env                 → DATABASE_URL, API_TOKEN, FLASK_ENV, PORT
  backend/__init__.py  → empty, makes backend a proper Python package

─── FINAL CHECKLIST ───────────────────────────────────────────
[ ] README.md is the FIRST key in fileStructure
[ ] frontend/index.html, vite.config.ts, tsconfig.json match templates exactly
[ ] frontend/src/main.tsx calls ReactDOM.createRoot
[ ] backend/models.py has 2+ domain-specific SQLAlchemy tables
[ ] backend/conftest.py uses SQLite in-memory for tests
[ ] One failing test per intentional bug (passes after fix)
[ ] All test files use vi.mock/vi.fn/vi.spyOn — never jest.*
[ ] No placeholder stubs anywhere
[ ] Most write routes use @require_auth — exactly ONE sensitive route is missing it
[ ] Frontend uses react-router-dom for navigation, @tanstack/react-query for data fetching

Return ONLY the JSON object. No prose, no markdown fences.
"""


# ── Generator ─────────────────────────────────────────────────────────────────
def generate_with_llm(
    job_role: str,
    experience_level: str,
    tech_stack: List[str],
    tasks: List[Dict[str, Any]],
    skills_to_test: Optional[List[str]] = None,
    problem_types: Optional[List[str]] = None,
    complexity: str = "medium",
    model: Optional[str] = None,
    company_name: str = "",
    job_description: str = "",
    validated_deps: Optional[Dict[str, str]] = None,
    variant_index: int = 0,
    total_variants: int = 1,
) -> Dict[str, Any]:
    """
    Generate project files using OpenAI.
    Returns a dict with 'fileStructure' (dict[path, content]) and 'intentionalIssues' (list).
    Safe fallback to empty on failure.
    """
    client, default_model = _make_client()
    if not client:
        logger.warning("LLM not available (missing OPENAI_API_KEY or openai package)")
        return {"fileStructure": {}, "intentionalIssues": []}

    try:
        prompt = _build_prompt(
            job_role, experience_level, tech_stack, tasks,
            skills_to_test or [], problem_types or [], complexity,
            company_name=company_name, job_description=job_description,
            validated_deps=validated_deps or {},
            variant_index=variant_index,
            total_variants=total_variants,
        )

        chosen_model = model or default_model

        # Use higher temperature for multi-variant calls to force structural diversity
        temperature = 1.1 if total_variants > 1 else 0.7

        resp = client.chat.completions.create(
            model=chosen_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,  # 1.1 for variants = more creative, diverse output
            response_format={"type": "json_object"},
            max_tokens=32000,        # richer codebases need more room
        )
        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        if not isinstance(data, dict):
            logger.error("LLM returned non-dict response; falling back")
            return {"fileStructure": {}, "intentionalIssues": []}

        # Support both structured {fileStructure, intentionalIssues} and flat {path: content}
        intentional_issues: List[Dict[str, Any]] = []
        if "fileStructure" in data and isinstance(data["fileStructure"], dict):
            raw_files = data["fileStructure"]
            intentional_issues = data.get("intentionalIssues") or []
        else:
            raw_files = {k: v for k, v in data.items() if k not in ("intentionalIssues",)}
            intentional_issues = data.get("intentionalIssues") or []

        # Normalize file contents to strings
        file_structure: Dict[str, str] = {}
        for k, v in raw_files.items():
            try:
                file_structure[str(k)] = str(v) if not isinstance(v, str) else v
            except Exception:
                continue

        # Post-process: inject pinned infrastructure files regardless of what the LLM produced
        # This guarantees Vite always starts, regardless of LLM version drift.
        has_frontend = any(k.startswith("frontend/") for k in file_structure)
        has_backend = any(k.startswith("backend/") for k in file_structure)

        if has_frontend:
            file_structure.setdefault("frontend/index.html", INDEX_HTML_TEMPLATE)
            file_structure.setdefault("frontend/vite.config.ts", VITE_CONFIG_TEMPLATE)
            file_structure.setdefault("frontend/tsconfig.json", TSCONFIG_TEMPLATE)
            file_structure.setdefault("frontend/tsconfig.node.json", TSCONFIG_NODE_TEMPLATE)
            file_structure.setdefault("frontend/src/test/setup.ts", TEST_SETUP_TEMPLATE)

        # Always inject .env and auth scaffold — every project needs these
        file_structure.setdefault(".env", ENV_TEMPLATE)
        if has_backend:
            file_structure.setdefault("backend/auth.py", AUTH_SCAFFOLD)
            file_structure.setdefault("backend/__init__.py", "")
            file_structure.setdefault("backend/routes/__init__.py", "")
            # Ensure package.json has the correct pinned deps
            pkg_key = "frontend/package.json"
            try:
                existing_pkg = json.loads(file_structure.get(pkg_key, "{}"))
                existing_pkg.setdefault("name", "frontend")
                existing_pkg.setdefault("version", "1.0.0")
                existing_pkg.setdefault("private", True)
                existing_pkg.setdefault("type", "module")
                existing_pkg.setdefault("scripts", {
                    "dev": "vite",
                    "build": "tsc && vite build",
                    "preview": "vite preview",
                    "test": "vitest run",
                    "test:watch": "vitest"
                })
                # Merge pinned deps — pinned versions always win
                existing_pkg["dependencies"] = {
                    **existing_pkg.get("dependencies", {}),
                    **REACT_VITE_DEPS["dependencies"]
                }
                existing_pkg["devDependencies"] = {
                    **existing_pkg.get("devDependencies", {}),
                    **REACT_VITE_DEPS["devDependencies"]
                }
                file_structure[pkg_key] = json.dumps(existing_pkg, indent=2)
            except Exception as e:
                logger.warning(f"Could not merge frontend/package.json: {e}")

        # Validate and enrich intentionalIssues schema
        # Required: id, description, file, line_hint, task_id, severity, category
        VALID_SEVERITIES = {"low", "medium", "high", "critical"}
        VALID_CATEGORIES = {
            "api_design", "data_layer", "frontend_state",
            "security", "accessibility", "performance", "testing"
        }
        validated_issues = []
        for issue in intentional_issues:
            if not isinstance(issue, dict):
                continue
            if not ("id" in issue and "description" in issue):
                logger.warning(f"Skipping malformed intentional issue: {issue}")
                continue
            severity = str(issue.get("severity", "medium")).lower()
            category = str(issue.get("category", "")).lower()
            validated_issues.append({
                "id": str(issue["id"]),
                "description": str(issue["description"]),
                "file": str(issue.get("file", "")),
                "line_hint": str(issue.get("line_hint", "")),
                "task_id": str(issue.get("task_id", "")),
                "severity": severity if severity in VALID_SEVERITIES else "medium",
                "category": category if category in VALID_CATEGORIES else "api_design",
                "expected_failing_test": str(issue.get("expected_failing_test", "")),
            })

        # Post-generation validation gate — reject before a candidate ever sees it
        errors = _validate_output(file_structure, validated_issues)
        if errors:
            logger.error(f"Generated output failed validation ({len(errors)} errors): {errors[:3]}")
            # Return what we have but flag it — caller can decide to retry or surface the errors
            return {
                "fileStructure": file_structure,
                "intentionalIssues": validated_issues,
                "validationErrors": errors,
                "valid": False,
            }

        logger.info(
            f"LLM generated {len(file_structure)} files and {len(validated_issues)} intentional issues "
            f"(model={chosen_model}) — validation passed"
        )
        # Compute scenario label for the legacy path so callers always get scenarioName
        try:
            scenario_entry = VARIANT_CATALOGUE[variant_index % len(VARIANT_CATALOGUE)]
            scenario_name = scenario_entry["scenario"].split("—")[0].strip()
        except Exception:
            scenario_name = f"Variant {variant_index}"

        return {
            "fileStructure": file_structure,
            "intentionalIssues": validated_issues,
            "valid": True,
            "variantIndex": variant_index,
            "scenarioName": scenario_name,
            "fileCount": len(file_structure),
            "issueCount": len(validated_issues),
        }

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return {"fileStructure": {}, "intentionalIssues": []}
