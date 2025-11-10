# MCP Server A: Job Analysis + Task Generator

## Overview
This MCP server handles job posting verification and assessment task generation.

## Structure
```
mcp_server_a/
├── server.py              # Main MCP server
├── agent_1_joblink_verifier.py
├── agent_2_assessment_generator.py
└── README.md
```

## Tools

1. **`verify_job_posting(url)`**
   - Validates job posting URL
   - Extracts job title, company, and description
   - Uses: `agent_1_joblink_verifier.py`

2. **`generate_assessments(jobTitle, company, jobDescription)`**
   - Generates 2-5 assessment tasks
   - Analyzes role, tech stack, and seniority
   - Uses: `agent_2_assessment_generator.py`

3. **`analyze_job_pipeline(url)`**
   - Complete end-to-end workflow
   - Verifies URL → extracts data → generates assessments

## Running

```bash
cd mcp_server_a
python server.py
```

## Dependencies

- `mcp>=1.0.0`
- `requests>=2.31.0`
- `beautifulsoup4>=4.12.0`

