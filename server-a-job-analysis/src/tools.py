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
            description="Generate customized assessment recommendations (2-3 templates) based on job data. Analyzes the role type (Frontend/Backend/Data/Full-Stack), tech stack, and seniority level to recommend relevant assessment templates with duration and components.",
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
        )
    ]

