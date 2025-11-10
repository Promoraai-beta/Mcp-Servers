# MCP Server B: Validator + Problem Generator + Builder

## Overview
This MCP server validates dependencies, generates LeetCode problems, and builds WebContainer structures.

## Structure
```
mcp_server_b/
├── server.py              # Main MCP server
├── agent_3_validator.py    # Dependency validation
├── agent_4_leetcode_generator.py  # Problem file generation
├── agent_5_builder.py     # WebContainer structure builder
└── README.md
```

## Tools

1. **`validate_dependencies(dependencies, techStack, packageManager)`**
   - Validates package names (npm, pip, maven, etc.)
   - Checks version compatibility
   - Returns validated dependencies with warnings
   - Uses: `agent_3_validator.py`

2. **`generate_leetcode_problems(tasks, techStack, language)`**
   - Creates individual problem files
   - Generates test files
   - Returns all problem files (task_1.js, task_1.test.js, etc.)
   - Uses: `agent_4_leetcode_generator.py`

3. **`build_webcontainer_structure(tasks, problems, validatedDeps, techStack, language)`**
   - Organizes files into complete folder structure
   - Creates package.json, README, configs
   - Returns complete fileStructure for WebContainer
   - Uses: `agent_5_builder.py`

## Running

```bash
cd mcp_server_b
python server.py
```

## Dependencies

- `mcp>=1.0.0`

