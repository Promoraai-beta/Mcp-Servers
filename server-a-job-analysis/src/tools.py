"""
MCP Tools Definitions for Server A
Contains all tool schemas and descriptions
"""

from mcp.types import Tool


def get_tools() -> list[Tool]:
    """
    Return list of available tools for Server A.
    """
    return [
        Tool(
            name="verify_job_posting",
            description="Validate a job posting URL and extract structured data. Scrapes the URL, analyzes the content to verify it's a valid job posting (not a job board listing), and extracts job title, company name, and full job description.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the job posting to verify and extract data from"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="generate_assessments",
            description="Generate customized assessment tasks (2-3) based on job data. Uses an LLM to analyse the role, tech stack, seniority level, and recruiter-selected component types (ide_project, leetcode, database, docs, sheets, design) to produce specific, rubric-ready tasks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "jobTitle": {
                        "type": "string",
                        "description": "Job title (e.g., 'Senior React Developer')"
                    },
                    "company": {
                        "type": "string",
                        "description": "Company name"
                    },
                    "jobDescription": {
                        "type": "string",
                        "description": "Full job description text"
                    },
                    "assessmentPreferences": {
                        "type": "object",
                        "description": "Recruiter-selected assessment configuration",
                        "properties": {
                            "components": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Enabled component types: ide_project, leetcode, database, docs, sheets, design"
                            },
                            "ideLanguage": {
                                "type": "string",
                                "description": "Primary language for ide_project tasks (e.g. typescript, python)"
                            },
                            "timeLimitMinutes": {
                                "type": "integer",
                                "description": "Total assessment time budget in minutes (default 60)"
                            }
                        }
                    }
                },
                "required": ["jobTitle", "company", "jobDescription"]
            }
        ),
        Tool(
            name="analyze_job_pipeline",
            description="Complete end-to-end job analysis workflow in a single call. First verifies the job posting URL and extracts job data, then automatically generates assessment recommendations based on the extracted information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the job posting to analyze"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="extract_skills",
            description="Extract skills, role, seniority level, and assessment configuration from a job title and description. Returns a structured list of detected skills (with categories), inferred role/level, recommended IDE language, suggested assessment component types, recommended task count, and suggested bug categories. Use this before generate_assessments to give the recruiter a preview and let them adjust settings.",
            inputSchema={
                "type": "object",
                "properties": {
                    "jobTitle": {
                        "type": "string",
                        "description": "Job title (e.g. 'Senior React Developer')"
                    },
                    "jobDescription": {
                        "type": "string",
                        "description": "Full job description text to extract skills from"
                    }
                },
                "required": ["jobTitle", "jobDescription"]
            }
        )
    ]

