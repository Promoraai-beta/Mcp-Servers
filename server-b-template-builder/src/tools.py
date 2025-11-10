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
                    "useLLM": {
                        "type": "boolean",
                        "description": "Use LLM to generate project (overrides env USE_LLM)",
                        "default": False
                    },
                    "llmModel": {
                        "type": "string",
                        "description": "LLM model to use (overrides env OPENAI_MODEL)",
                        "default": "gpt-4o-mini"
                    }
                },
                "required": ["tasks", "techStack"]
            }
        )
    ]

