"""
Agent 4: LeetCode Problem Generator
Generates individual problem files with starter code and test files.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def generate_leetcode_problems(tasks: List[Dict[str, Any]], tech_stack: List[str], language: str = "javascript") -> Dict[str, str]:
    """
    Generate LeetCode-style problem files for each task.
    
    Args:
        tasks: List of assessment tasks
        tech_stack: List of technologies
        language: Programming language ('javascript', 'python', 'java', 'typescript')
    
    Returns:
        Dictionary mapping file paths to file contents
    """
    try:
        logger.info(f"Generating {len(tasks)} LeetCode problems in {language}")
        
        problems = {}
        tasks_dir = "problems"
        
        # Determine file extension
        lang_ext = {
            "javascript": "js",
            "typescript": "ts",
            "python": "py",
            "java": "java"
        }.get(language.lower(), "js")
        
        # Create main README
        readme_content = "# Assessment Problems\n\n"
        readme_content += f"Solve each problem in the `{tasks_dir}/` directory.\n\n"
        readme_content += "## Problems:\n\n"
        
        for idx, task in enumerate(tasks, 1):
            task_id = f"task_{idx}"
            task_title = task.get("title", f"Problem {idx}")
            duration = task.get("duration", "Not specified")
            components = task.get("components", [])
            description = task.get("description", "")
            
            readme_content += f"### Problem {idx}: {task_title}\n"
            readme_content += f"- **Duration:** {duration}\n"
            readme_content += f"- **File:** `{tasks_dir}/{task_id}.{lang_ext}`\n"
            readme_content += f"- **Test File:** `{tasks_dir}/{task_id}.test.{lang_ext}`\n"
            if components:
                readme_content += f"- **Requirements:**\n"
                for comp in components:
                    readme_content += f"  - {comp}\n"
            if description:
                readme_content += f"- **Description:** {description}\n"
            readme_content += "\n"
        
        readme_content += "## How to Solve:\n\n"
        readme_content += "1. Open each problem file in the `problems/` directory\n"
        readme_content += "2. Implement your solution in the provided function\n"
        readme_content += "3. Run tests using: `npm test` or `npm run test`\n"
        readme_content += "4. Submit your solution when ready\n\n"
        
        problems[f"{tasks_dir}/README.md"] = readme_content
        
        # Generate problem files for each task
        for idx, task in enumerate(tasks, 1):
            task_id = f"task_{idx}"
            task_title = task.get("title", f"Problem {idx}")
            components = task.get("components", [])
            description = task.get("description", "")
            
            # Create problem file with starter code
            problem_file = f"{tasks_dir}/{task_id}.{lang_ext}"
            starter_code = _generate_starter_code(task_id, task_title, components, description, lang_ext)
            problems[problem_file] = starter_code
            
            # Create test file
            test_file = f"{tasks_dir}/{task_id}.test.{lang_ext}"
            test_code = _generate_test_code(task_id, task_title, idx, lang_ext)
            problems[test_file] = test_code
        
        logger.info(f"Generated {len(problems)} problem files")
        return problems
    
    except Exception as e:
        logger.error(f"Error generating LeetCode problems: {e}")
        return {}


def _generate_starter_code(task_id: str, title: str, components: List[str], description: str, lang_ext: str) -> str:
    """Generate starter code for a problem."""
    if lang_ext == "py":
        code = f"""# Problem: {title}
# Duration: Not specified

# TODO: Implement the solution
# Requirements:
"""
        for comp in components:
            code += f"# - {comp}\n"
        if description:
            code += f"\n# Description: {description}\n"
        code += "\n# Your solution here:\n"
        code += "def solution():\n    \"\"\"\n    Implement your solution here.\n    \"\"\"\n    pass\n"
        code += "\n# Example usage:\n# result = solution()\n"
    
    elif lang_ext == "ts":
        code = f"""// Problem: {title}
// Duration: Not specified

// TODO: Implement the solution
// Requirements:
"""
        for comp in components:
            code += f"// - {comp}\n"
        if description:
            code += f"\n// Description: {description}\n"
        code += "\n// Your solution here:\n"
        code += "function solution(): any {\n    // Your code here\n    return null;\n}\n\nexport default solution;\n"
        code += "\n// Example usage:\n// const result = solution();\n"
    
    elif lang_ext == "js":
        code = f"""// Problem: {title}
// Duration: Not specified

// TODO: Implement the solution
// Requirements:
"""
        for comp in components:
            code += f"// - {comp}\n"
        if description:
            code += f"\n// Description: {description}\n"
        code += "\n// Your solution here:\n"
        code += "function solution() {\n    // Your code here\n    return null;\n}\n\nexport default solution;\n"
        code += "\n// Example usage:\n// const result = solution();\n"
    
    elif lang_ext == "java":
        code = f"""// Problem: {title}
// Duration: Not specified

// TODO: Implement the solution
// Requirements:
"""
        for comp in components:
            code += f"// - {comp}\n"
        if description:
            code += f"\n// Description: {description}\n"
        code += "\npublic class Solution {\n    public Object solution() {\n        // Your code here\n        return null;\n    }\n}\n"
    
    return code


def _generate_test_code(task_id: str, title: str, idx: int, lang_ext: str) -> str:
    """Generate test code for a problem."""
    if lang_ext == "py":
        return f"""import pytest
from {task_id} import solution

def test_solution():
    # TODO: Add visible test cases
    # These tests will be shown to the candidate
    result = solution()
    assert result is not None
    # Add more test cases here
"""
    
    elif lang_ext in ["js", "ts"]:
        return f"""import solution from './{task_id}';

describe('Problem {idx}: {title}', () => {{
    test('should solve the problem', () => {{
        // TODO: Add visible test cases
        // These tests will be shown to the candidate
        const result = solution();
        expect(result).toBeDefined();
        // Add more test cases here
    }});
}});
"""
    
    elif lang_ext == "java":
        return f"""// Test file for Problem {idx}: {title}
// TODO: Add JUnit tests here
"""
    
    return ""

