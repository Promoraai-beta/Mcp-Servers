import json
import logging
from typing import Any

from mcp.types import TextContent

from agents.agent_1_joblink_verifier import run_agent_1
from agents.agent_2_assessment_generator import run_agent_2
from agents.agent_skills_extractor import run_skills_extractor

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
    company   = arguments.get("company", "")
    job_description = arguments.get("jobDescription")
    assessment_preferences = arguments.get("assessmentPreferences") or {}

    if not job_title or not job_description:
        raise ValueError("jobTitle and jobDescription are required")

    job_data = {
        "jobTitle":              job_title,
        "company":               company,
        "jobDescription":        job_description,
        "assessmentPreferences": assessment_preferences,
    }

    logger.info(
        f"Generating assessments for '{job_title}' at '{company}' "
        f"| components={assessment_preferences.get('components', ['ide_project', 'docs'])}"
    )
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


async def handle_extract_skills(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle extract_skills tool call."""
    job_title = arguments.get("jobTitle")
    job_description = arguments.get("jobDescription")

    if not job_title or not job_description:
        raise ValueError("jobTitle and jobDescription are required")

    logger.info(f"Extracting skills for: '{job_title}'")
    result = run_skills_extractor(job_title, job_description)

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


# Tool handler mapping
TOOL_HANDLERS = {
    "verify_job_posting":  handle_verify_job_posting,
    "generate_assessments": handle_generate_assessments,
    "analyze_job_pipeline": handle_analyze_job_pipeline,
    "extract_skills":       handle_extract_skills,
}

