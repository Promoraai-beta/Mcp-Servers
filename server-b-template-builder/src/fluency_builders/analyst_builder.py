"""
Product / Analyst AI Fluency Builder
Creates a data-analysis workspace (10+ files) with:
- Messy CSV data
- Ambiguous brief
- AI-generated summary with errors
- Contradictory requirements
- Structured checkpoints
"""

import json
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


class AnalystFluencyBuilder:
    """Builds Product/Analyst AI fluency simulation."""

    def build(self, role_id: str, difficulty: str = "medium", **kwargs) -> Dict[str, Any]:
        file_structure = self._get_base_template()
        bug_files, intentional_issues = self._inject_issues(difficulty)
        file_structure.update(bug_files)

        return {
            "projectStructure": file_structure,
            "projectMetadata": {"role": role_id, "displayName": "Product Analyst", "difficulty": difficulty, "estimatedMinutes": 45},
            "intentionalIssues": intentional_issues,
            "evaluationCriteria": {
                "data_validation": "Did they notice bad data (outliers, missing values)?",
                "ai_critique": "Did they find errors in the AI-generated summary?",
                "assumption_checking": "Did they question contradictory requirements?",
                "communication": "Is their analysis clear and well-structured?",
                "reasoning": "Did they justify conclusions with evidence?",
            },
            "candidateInstructions": (
                "You're an analyst reviewing an AI-generated report. The data has issues, "
                "the brief is ambiguous, and the AI summary has errors. "
                "Open the data viewer with `npm start`. Validate everything. "
                "Write your analysis in ANALYSIS.md."
            ),
            "setupInstructions": "npm install && npm start",
        }

    # ── Base template ──────────────────────────────────────────────

    def _get_base_template(self) -> Dict[str, str]:
        return {
            "package.json": json.dumps({
                "name": "analyst-fluency-assessment",
                "version": "1.0.0",
                "private": True,
                "scripts": {"start": "npx serve . -l 3000"},
                "dependencies": {"serve": "^14.2.0"},
            }, indent=2),
            "index.html": (
                '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
                '  <meta charset="UTF-8"><title>Data Analysis Workspace</title>\n'
                '  <style>\n'
                '    body { font-family: system-ui; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }\n'
                '    table { width: 100%; border-collapse: collapse; margin: 1rem 0; }\n'
                '    th, td { border: 1px solid #ddd; padding: 0.5rem; text-align: left; }\n'
                '    th { background: #f5f5f5; }\n'
                '    .warn { color: #e65100; }\n'
                '    pre { background: #f5f5f5; padding: 1rem; overflow-x: auto; }\n'
                '  </style>\n'
                '</head>\n<body>\n'
                '  <h1>Data Analysis Workspace</h1>\n'
                '  <p>Review the files in this project. Open <code>brief.md</code>, '
                '<code>data/sales.csv</code>, and <code>ai_summary.md</code>.</p>\n'
                '  <p>Write your analysis in <code>ANALYSIS.md</code>.</p>\n'
                '  <div id="data-preview"></div>\n'
                '  <script src="viewer.js"></script>\n'
                '</body>\n</html>'
            ),
            "viewer.js": (
                "// Simple CSV viewer\n"
                "fetch('data/sales.csv')\n"
                "  .then(r => r.text())\n"
                "  .then(csv => {\n"
                "    const rows = csv.trim().split('\\n').map(r => r.split(','));\n"
                "    const [headers, ...data] = rows;\n"
                "    let html = '<h2>Sales Data Preview (first 20 rows)</h2><table><tr>';\n"
                "    headers.forEach(h => html += `<th>${h.trim()}</th>`);\n"
                "    html += '</tr>';\n"
                "    data.slice(0, 20).forEach(row => {\n"
                "      html += '<tr>';\n"
                "      row.forEach(cell => html += `<td>${cell.trim()}</td>`);\n"
                "      html += '</tr>';\n"
                "    });\n"
                "    html += '</table>';\n"
                "    if (data.length > 20) html += `<p class=\"warn\">${data.length - 20} more rows not shown.</p>`;\n"
                "    document.getElementById('data-preview').innerHTML = html;\n"
                "  });\n"
            ),
            # Template for candidate's answer
            "ANALYSIS.md": (
                "# Your Analysis\n\n"
                "## Data Quality Issues Found\n"
                "(document issues here)\n\n"
                "## Errors in AI Summary\n"
                "(document errors here)\n\n"
                "## Revised Insights\n"
                "(your corrected conclusions)\n\n"
                "## Assumptions & Limitations\n"
                "(list your assumptions)\n\n"
                "## Recommendations\n"
                "(your recommendations based on corrected data)\n"
            ),
        }

    # ── Issue injection ────────────────────────────────────────────

    def _inject_issues(self, difficulty: str) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        tier = {"easy": 3, "medium": 5, "hard": 7}.get(difficulty, 5)
        issues: List[Dict[str, Any]] = []
        files: Dict[str, str] = {}

        # ── brief.md — ambiguous and contradictory ──
        files["brief.md"] = (
            "# Product Brief: Q4 Sales Performance Review\n\n"
            "## Objective\n"
            "Analyze Q4 2024 sales data and provide recommendations for Q1 2025 strategy.\n\n"
            "## Key Questions\n"
            "1. Which region had the highest growth?\n"
            "2. What was the average deal size by product category?\n"
            "3. Which sales reps are underperforming?\n\n"
            "## Constraints\n"
            "- Focus on recurring revenue only (ignore one-time deals)\n"
            "- Use the attached dataset as the single source of truth\n\n"
            "## Notes from Stakeholders\n"
            "- VP Sales: \"West region is our biggest growth area — make sure the data shows that.\"\n"
            "- CFO: \"I only care about deals above $10k. Small deals are noise.\"\n"
            "- CEO: \"I want to see ALL deals — we need the full picture.\"\n\n"
            "## Success Criteria\n"
            "- Clear summary with data-backed conclusions\n"
            "- Identify top 3 actionable recommendations\n"
        )
        issues.append({"id": "issue_contradictory_stakeholders", "description": "CFO says ignore small deals, CEO says include all deals — contradictory"})
        issues.append({"id": "issue_biased_directive", "description": "VP Sales explicitly biases the analysis toward West region"})

        # ── data/sales.csv — messy data with outliers and errors ──
        csv_rows = [
            "date,region,product,amount,deal_type,rep_name,rep_id",
            "2024-10-01,West,Enterprise,45000,recurring,Sarah Chen,R001",
            "2024-10-03,East,Starter,2500,recurring,Mike Johnson,R002",
            "2024-10-05,West,Pro,15000,recurring,Sarah Chen,R001",
            "2024-10-07,Central,Enterprise,52000,one-time,James Lee,R003",
            "2024-10-10,East,Pro,18000,recurring,Mike Johnson,R002",
            "2024-10-12,West,Starter,3200,recurring,Lisa Park,R004",
            "2024-10-15,Central,Pro,22000,recurring,James Lee,R003",
            "2024-10-18,East,Enterprise,67000,recurring,Amy Wu,R005",
            "2024-10-20,West,Enterprise,48000,recurring,Sarah Chen,R001",
            "2024-10-22,,Pro,19000,recurring,Mike Johnson,R002",  # missing region
            "2024-10-25,West,Pro,14000,recurring,Lisa Park,R004",
            "2024-10-28,East,Starter,2800,one-time,Amy Wu,R005",
            "2024-11-01,West,Enterprise,950000,recurring,Sarah Chen,R001",  # obvious outlier
            "2024-11-03,Central,Pro,21000,recurring,James Lee,R003",
            "2024-11-05,West,Starter,3500,recurring,Lisa Park,R004",
            "2024-11-08,East,Enterprise,55000,recurring,Mike Johnson,R002",
            "2024-11-10,Central,Enterprise,49000,recurring,James Lee,R003",
            "2024-11-12,West,Pro,17000,recurring,Sarah Chen,R001",
            "2024-11-15,East,Pro,-5000,recurring,Amy Wu,R005",  # negative amount
            "2024-11-18,West,Enterprise,43000,recurring,Lisa Park,R004",
            "2024-11-20,Central,Starter,2900,recurring,James Lee,R003",
            "2024-11-22,East,Enterprise,61000,recurring,Amy Wu,R005",
            "2024-11-25,west,Pro,16000,recurring,Sarah Chen,R001",  # lowercase region
            "2024-11-28,West,Pro,20000,recurring,Lisa Park,R004",
            "2024-12-01,East,Enterprise,58000,recurring,Mike Johnson,R002",
            "2024-12-03,Central,Pro,24000,one-time,James Lee,R003",
            "2024-12-05,West,Starter,3100,recurring,Sarah Chen,R001",
            "2024-12-08,East,Pro,19500,recurring,Amy Wu,R005",
            "2024-12-10,West,Enterprise,51000,recurring,Lisa Park,R004",
            "2024-12-12,Central,Starter,2700,recurring,James Lee,R003",
            "2024-12-15,West,Pro,18500,recurring,Sarah Chen,R001",
            "2024-12-18,East,Enterprise,64000,recurring,Mike Johnson,R002",
            "2024-12-20,West,Enterprise,47000,recurring,Lisa Park,R004",
            "2024-12-22,Central,Pro,23000,recurring,James Lee,R003",
            "2024-12-28,East,Starter,,recurring,Amy Wu,R005",  # missing amount
        ]
        files["data/sales.csv"] = "\n".join(csv_rows) + "\n"

        issues.append({"id": "issue_missing_data", "description": "CSV has missing values: blank region (row 10), blank amount (last row)"})
        issues.append({"id": "issue_outlier", "description": "$950,000 deal (row 13) is a likely data entry error — 10x normal Enterprise deal"})
        issues.append({"id": "issue_negative_amount", "description": "Negative $5,000 amount (row 19) — likely refund or error"})

        if tier >= 4:
            issues.append({"id": "issue_inconsistent_region", "description": "'west' (lowercase) vs 'West' — inconsistent casing"})

        # ── ai_summary.md — AI-generated report with errors ──
        files["ai_summary.md"] = (
            "# Q4 2024 Sales Performance Summary\n"
            "*Generated by AI Assistant*\n\n"
            "## Key Findings\n\n"
            "1. **Total Q4 Revenue: $1,847,200** (across all deal types)\n"
            "2. **West region led with $1,258,300** in total revenue (68% of total)\n"
            "3. **Enterprise product had the highest average deal size: $53,400**\n"
            "4. **Sarah Chen was the top performer** with $1,105,500 in total sales\n"
            "5. **East region showed 15% quarter-over-quarter growth**\n\n"
            "## Regional Breakdown\n"
            "| Region | Total Revenue | Deal Count | Avg Deal Size |\n"
            "|--------|-------------|------------|---------------|\n"
            "| West | $1,258,300 | 14 | $89,878 |\n"
            "| East | $362,800 | 10 | $36,280 |\n"
            "| Central | $197,600 | 8 | $24,700 |\n\n"
            "## Recommendations\n"
            "1. Double down on West region — it's clearly the growth driver\n"
            "2. Invest more in Enterprise product sales training\n"
            "3. Consider performance improvement plans for underperformers\n\n"
            "## Methodology\n"
            "All calculations include every transaction in the dataset.\n"
        )
        issues.append({"id": "issue_ai_includes_outlier", "description": "AI summary includes the $950k outlier — inflates West region and Sarah Chen's numbers"})
        issues.append({"id": "issue_ai_includes_one_time", "description": "AI summary includes one-time deals despite brief saying to focus on recurring only"})

        if tier >= 5:
            issues.append({"id": "issue_ai_wrong_growth", "description": "AI claims 15% East growth but no prior quarter data exists to compare"})

        if tier >= 6:
            # ── CHECKPOINTS.md — structured prompts for candidate responses ──
            files["CHECKPOINTS.md"] = (
                "# Analysis Checkpoints\n\n"
                "## Checkpoint 1: Data Quality\n"
                "Before analyzing, list all data quality issues you find in `data/sales.csv`.\n\n"
                "## Checkpoint 2: AI Summary Critique\n"
                "Read `ai_summary.md`. List every factual error or questionable claim.\n\n"
                "## Checkpoint 3: Stakeholder Conflicts\n"
                "The brief has conflicting directives. How would you handle them?\n\n"
                "## Checkpoint 4: Corrected Analysis\n"
                "Produce your own summary with correct numbers (after cleaning data).\n\n"
                "## Checkpoint 5: Recommendations\n"
                "Give 3 data-backed recommendations. Explain assumptions.\n"
            )
            issues.append({"id": "issue_ai_deal_count_wrong", "description": "AI says West has 14 deals but actual count differs after excluding one-time deals"})

        if tier >= 7:
            # ── second dataset with different story ──
            files["data/support_tickets.csv"] = (
                "date,region,product,ticket_type,severity,resolution_hours\n"
                "2024-10-05,West,Enterprise,bug,high,48\n"
                "2024-10-12,West,Enterprise,feature_request,low,2\n"
                "2024-10-20,East,Pro,bug,medium,12\n"
                "2024-11-01,West,Enterprise,bug,critical,72\n"
                "2024-11-15,Central,Pro,bug,low,4\n"
                "2024-12-01,West,Enterprise,bug,high,36\n"
                "2024-12-10,West,Enterprise,bug,critical,96\n"
                "2024-12-20,East,Starter,feature_request,low,1\n"
            )
            issues.append({"id": "issue_support_contradicts_sales", "description": "Support data shows West Enterprise has critical bugs — contradicts 'double down on West' recommendation"})

        files["README.md"] = self._get_readme()

        return files, issues

    # ── README ─────────────────────────────────────────────────────

    def _get_readme(self) -> str:
        return """# Analyst AI Fluency Assessment

## Scenario
Your team used AI to generate a quarterly sales report. You need to verify
the analysis, find errors, and produce a corrected version.

## Instructions
1. **Open the workspace** — `npm install && npm start` (opens a data viewer on port 3000)
2. **Read the brief** — `brief.md` describes what stakeholders want
3. **Examine the data** — `data/sales.csv` (look carefully for quality issues)
4. **Critique the AI summary** — `ai_summary.md` has errors — find them all
5. **Write your analysis** — Put your corrected analysis in `ANALYSIS.md`

## What we're measuring
- Do you validate data before drawing conclusions?
- Do you catch errors in AI-generated summaries?
- How do you handle contradictory stakeholder requirements?
- Are your conclusions backed by evidence?
- Do you communicate assumptions and limitations clearly?

Good luck.
"""
