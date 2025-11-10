"""
MCP Tool Handlers for Server A
Contains the actual tool execution logic
"""

import json
import logging
from typing import Any

from mcp.types import TextContent

from agents.agent_1_joblink_verifier import run_agent_1
import os
from agents.agent_2_assessment_generator import run_agent_2
from llm_assessment import generate_assessments_with_llm

logger = logging.getLogger(__name__)


async def handle_verify_job_posting(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle verify_job_posting tool call."""
    url = arguments.get("url")
    if not url:
        raise ValueError("url is required")
    
    logger.info(f"Verifying job posting: {url}")
    result = run_agent_1(url)
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_generate_assessments(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle generate_assessments tool call."""
    job_title = arguments.get("jobTitle")
    company = arguments.get("company")
    job_description = arguments.get("jobDescription")
    
    if not all([job_title, company, job_description]):
        raise ValueError("jobTitle, company, and jobDescription are required")
    
    job_data = {
        "jobTitle": job_title,
        "company": company,
        "jobDescription": job_description
    }
    
    logger.info(f"Generating assessments for {job_title} at {company}")
    use_llm = os.environ.get("USE_LLM", "false").lower() == "true"
    result = {}
    if use_llm:
        logger.info("USE_LLM=true → using LLM for assessment generation")
        result = generate_assessments_with_llm(job_title, company, job_description) or {}
    if not result:
        # Fallback to deterministic agent
        result = run_agent_2(job_data)
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_analyze_job_pipeline(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle analyze_job_pipeline tool call."""
    url = arguments.get("url")
    if not url:
        raise ValueError("url is required")
    
    logger.info(f"Analyzing job pipeline for: {url}")
    
    # Step 1: Verify job posting
    verification_result = run_agent_1(url)
    
    if not verification_result.get("isValidJobPage", False):
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Invalid job posting URL",
                "verification": verification_result
            }, indent=2)
        )]
    
    # Step 2: Generate assessments
    job_data = {
        "jobTitle": verification_result.get("jobTitle", ""),
        "company": verification_result.get("company", ""),
        "jobDescription": verification_result.get("jobDescription", "")
    }
    
    use_llm = os.environ.get("USE_LLM", "false").lower() == "true"
    if use_llm:
        logger.info("USE_LLM=true → using LLM in pipeline for assessment generation")
        assessment_result = generate_assessments_with_llm(
            job_data["jobTitle"], job_data["company"], job_data["jobDescription"]
        ) or run_agent_2(job_data)
    else:
        assessment_result = run_agent_2(job_data)
    
    # Combine results
    pipeline_result = {
        "verification": verification_result,
        "assessments": assessment_result
    }
    
    return [TextContent(
        type="text",
        text=json.dumps(pipeline_result, indent=2)
    )]


# Tool handler mapping
TOOL_HANDLERS = {
    "verify_job_posting": handle_verify_job_posting,
    "generate_assessments": handle_generate_assessments,
    "analyze_job_pipeline": handle_analyze_job_pipeline
}

