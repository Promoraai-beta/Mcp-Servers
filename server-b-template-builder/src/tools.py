"""
MCP Tools Definitions for Server B
Contains all tool schemas and descriptions
"""

from mcp.types import Tool


def get_tools() -> list[Tool]:
    """
    Return list of available tools for Server B.
    """
    return [
        Tool(
            name="validate_dependencies",
            description="Validates package names (npm, pip, maven, etc.) and checks version compatibility. Returns validated dependencies with warnings for invalid packages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dependencies": {
                        "type": "object",
                        "description": "Dictionary of package names to versions",
                        "additionalProperties": {"type": "string"}
                    },
                    "techStack": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of technologies used in the project"
                    },
                    "packageManager": {
                        "type": "string",
                        "enum": ["npm", "pip", "maven", "yarn"],
                        "description": "Package manager to use",
                        "default": "npm"
                    }
                },
                "required": ["dependencies", "techStack"]
            }
        ),
        Tool(
            name="generate_leetcode_problems",
            description="Generates individual problem files with starter code and test files for each task. Creates problems/task_X.js, task_X.test.js, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of assessment tasks"
                    },
                    "techStack": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of technologies"
                    },
                    "language": {
                        "type": "string",
                        "enum": ["javascript", "typescript", "python", "java"],
                        "description": "Programming language",
                        "default": "javascript"
                    }
                },
                "required": ["tasks", "techStack"]
            }
        ),
        Tool(
            name="build_webcontainer_structure",
            description="Builds complete WebContainer structure with all files, dependencies, and configuration. Combines validated dependencies, generated problems, and creates the full file structure with intentional bugs for role-based assessments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of assessment tasks"
                    },
                    "problems": {
                        "type": "object",
                        "description": "Generated problem files (optional)",
                        "additionalProperties": {"type": "string"}
                    },
                    "validatedDeps": {
                        "type": "object",
                        "description": "Validated dependencies (optional)",
                        "additionalProperties": {"type": "string"}
                    },
                    "techStack": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of technologies"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language",
                        "default": "javascript"
                    },
                    "jobRole": {
                        "type": "string",
                        "description": "Job role (e.g., 'Frontend Developer')"
                    },
                    "experienceLevel": {
                        "type": "string",
                        "description": "Experience level (e.g., 'Mid-level')"
                    },
                    "skillsToTest": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Skills to assess"
                    },
                    "problemTypes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of problems to inject"
                    },
                    "complexity": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                        "description": "Complexity level",
                        "default": "medium"
                    },
                    "variantIndex": {
                        "type": "integer",
                        "description": "Variant index for scenario selection (0-based)",
                        "default": 0
                    },
                    "totalVariants": {
                        "type": "integer",
                        "description": "Total number of variants being generated in this batch",
                        "default": 1
                    }
                },
                "required": ["tasks", "techStack"]
            }
        ),
        Tool(
            name="orchestrate_single_variant",
            description="OpenAI Agents SDK pipeline: generates one fresh unique code template for a single candidate invite. Runs TemplateBuilderAgent with the job context and returns fileStructure + intentionalIssues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "jobRole": {"type": "string", "description": "Job role"},
                    "techStack": {"type": "array", "items": {"type": "string"}, "description": "Tech stack"},
                    "experienceLevel": {"type": "string", "description": "Experience level", "default": "Mid-level"},
                    "complexity": {"type": "string", "enum": ["easy", "medium", "hard"], "default": "medium"},
                    "companyName": {"type": "string", "description": "Company name for domain inference"},
                    "jobDescription": {"type": "string", "description": "Job description text"},
                    "tasks": {"type": "array", "items": {"type": "object"}, "description": "Assessment tasks from Server A"},
                    "validatedDeps": {"type": "object", "description": "Pre-validated dependencies"},
                    "variantIndex": {"type": "integer", "description": "Variant slot index", "default": 0}
                },
                "required": ["jobRole", "techStack"]
            }
        ),
        Tool(
            name="orchestrate_bulk_variants",
            description="OpenAI Agents SDK pipeline: generates up to 10 unique code templates in parallel for a bulk invite batch. 500 candidates → ≤10 parallel LLM calls, round-robin assigned. Returns array of variants.",
            inputSchema={
                "type": "object",
                "properties": {
                    "jobRole": {"type": "string", "description": "Job role"},
                    "techStack": {"type": "array", "items": {"type": "string"}, "description": "Tech stack"},
                    "variantCount": {"type": "integer", "description": "Number of unique variants to generate (capped at 10)", "default": 1},
                    "experienceLevel": {"type": "string", "description": "Experience level", "default": "Mid-level"},
                    "complexity": {"type": "string", "enum": ["easy", "medium", "hard"], "default": "medium"},
                    "companyName": {"type": "string", "description": "Company name for domain inference"},
                    "jobDescription": {"type": "string", "description": "Job description text"},
                    "tasks": {"type": "array", "items": {"type": "object"}, "description": "Assessment tasks from Server A"},
                    "validatedDeps": {"type": "object", "description": "Pre-validated dependencies"}
                },
                "required": ["jobRole", "techStack"]
            }
        ),
    ]

