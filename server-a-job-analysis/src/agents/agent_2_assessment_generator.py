"""
Agent 2: Assessment Generator
Part of the Promora AI-powered hiring platform

This agent takes structured job data and recommends 2-3 assessment templates
based on the role, tech stack, and seniority level.
"""

import json
import logging
from typing import Dict, List, Any, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_agent_2(job_data: dict) -> dict:
    """
    Run Agent 2: Assessment Generator to recommend assessment templates.
    
    This function analyzes job data from Agent 1 and generates 2-3 tailored
    assessment templates based on simple keyword matching rules.
    
    Args:
        job_data (dict): Structured job data from Agent 1 containing:
            - jobTitle (str): The job title
            - company (str): Company name
            - jobDescription (str): Full job description text
            
    Returns:
        dict: Assessment recommendations containing:
            - suggestedAssessments (list): 2-3 recommended assessment templates
            - role (str): Detected role category
            - stack (list): Extracted technologies
            - level (str): Inferred seniority level
            
    Example:
        >>> job_data = {
        ...     "jobTitle": "Senior Python Developer",
        ...     "company": "TechCorp",
        ...     "jobDescription": "We need a senior Python developer with Django, React, and AWS experience..."
        ... }
        >>> result = run_agent_2(job_data)
        >>> print(result["suggestedAssessments"])
        [
            {
                "title": "Python + Django Challenge",
                "duration": "60 min",
                "components": ["API Development", "Database Design", "Testing"]
            }
        ]
    """
    try:
        logger.info("Starting Agent 2: Assessment Generator")
        
        # Validate input data
        if not _is_valid_job_data(job_data):
            logger.warning("Invalid job data provided")
            return {"suggestedAssessments": []}
        
        # Parse job information using simple keyword matching
        logger.info("Parsing job data...")
        role = _parse_role(job_data)
        stack = _parse_stack(job_data)
        level = _parse_level(job_data)
        
        logger.info(f"Detected: {role} role, {level} level, stack: {', '.join(stack)}")
        
        # Generate assessments using predefined mappings
        logger.info("Generating assessments using predefined rules...")
        suggested_assessments = _generate_suggested_assessments(role, stack, level)
        
        # Generate full template specification with task-specific files
        logger.info("Generating template specification with task files...")
        template_spec = _generate_template_spec(role, stack, level, suggested_assessments)
        
        result = {
            "suggestedAssessments": suggested_assessments,
            "role": role,
            "stack": stack,
            "level": level,
            "templateSpec": template_spec  # Add full template spec
        }
        
        logger.info(f"Agent 2 completed successfully. Generated {len(suggested_assessments)} assessments and template spec")
        return result
        
    except Exception as e:
        logger.error(f"Error in Agent 2: {str(e)}")
        return {"suggestedAssessments": []}


def _is_valid_job_data(job_data: dict) -> bool:
    """
    Validate that job data contains required fields.
    
    Args:
        job_data (dict): Job data to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(job_data, dict):
        return False
    
    required_fields = ["jobTitle", "company", "jobDescription"]
    return all(field in job_data for field in required_fields)


def _parse_role(job_data: dict) -> str:
    """
    Parse role using simple keyword matching rules.
    
    Args:
        job_data (dict): Job data containing title and description
        
    Returns:
        str: Detected role category
    """
    title = job_data.get('jobTitle', '').lower()
    description = job_data.get('jobDescription', '').lower()
    text = f"{title} {description}"
    
    # Priority 1: Check title first (most reliable indicator)
    if any(keyword in title for keyword in ["frontend", "front-end", "front end", "ui developer", "ui engineer"]):
        return "Frontend"
    
    if any(keyword in title for keyword in ["backend", "back-end", "back end", "server", "api engineer"]):
        return "Backend"
    
    if any(keyword in title for keyword in ["data", "machine learning", "ml engineer", "ai engineer", "analyst", "scientist"]):
        return "Data"
    
    if any(keyword in title for keyword in ["full-stack", "fullstack", "full stack"]):
        return "Full-Stack"
    
    # Priority 2: Check description with more specific keywords
    # Frontend keywords (more specific to avoid false positives)
    if any(keyword in description for keyword in ["frontend", "front-end", "react", "vue", "angular", "ui/ux", "ui development"]):
        return "Frontend"
    
    # Backend keywords (more specific)
    if any(keyword in description for keyword in ["backend", "back-end", "api development", "server-side", "rest api", "django", "flask", "express"]):
        return "Backend"
    
    # Data keywords
    if any(keyword in description for keyword in ["data", "machine learning", "ai", "analyst", "scientist"]):
        return "Data"
    
    # Full-stack keywords
    if any(keyword in description for keyword in ["full-stack", "fullstack", "full stack"]):
        return "Full-Stack"
    
    # Default fallback
    return "General"


def _parse_stack(job_data: dict) -> List[str]:
    """
    Parse tech stack using simple keyword matching rules.
    
    Args:
        job_data (dict): Job data containing description
        
    Returns:
        List[str]: List of detected technologies
    """
    text = job_data.get("jobDescription", "").lower()
    stack = []
    
    # Rule 1: Programming languages
    languages = ["python", "javascript", "java", "typescript", "go", "rust", "php", "ruby"]
    for lang in languages:
        if lang in text:
            stack.append(lang.title())
    
    # Rule 2: Frontend frameworks
    frontend = ["react", "vue", "angular", "html", "css"]
    for tech in frontend:
        if tech in text:
            stack.append(tech.title())
    
    # Rule 3: Backend frameworks
    backend = ["django", "flask", "express", "spring", "rails"]
    for tech in backend:
        if tech in text:
            stack.append(tech.title())
    
    # Rule 4: Databases
    databases = ["postgresql", "mysql", "mongodb", "redis", "sql"]
    for db in databases:
        if db in text:
            stack.append(db.title())
    
    # Rule 5: Cloud/DevOps
    cloud = ["aws", "azure", "docker", "kubernetes"]
    for tech in cloud:
        if tech in text:
            stack.append(tech.title())
    
    return list(set(stack))  # Remove duplicates


def _parse_level(job_data: dict) -> str:
    """
    Parse seniority level using simple keyword matching rules.
    
    Args:
        job_data (dict): Job data containing title and description
        
    Returns:
        str: Inferred seniority level
    """
    text = f"{job_data.get('jobTitle', '')} {job_data.get('jobDescription', '')}".lower()
    
    # Rule 1: Intern keywords
    if any(keyword in text for keyword in ["intern", "internship", "entry level"]):
        return "Intern"
    
    # Rule 2: Junior keywords
    if any(keyword in text for keyword in ["junior", "0-2 years", "1-2 years"]):
        return "Junior"
    
    # Rule 3: Senior keywords
    if any(keyword in text for keyword in ["senior", "lead", "5+ years", "6+ years"]):
        return "Senior"
    
    # Rule 4: Staff/Principal keywords
    if any(keyword in text for keyword in ["staff", "principal", "8+ years", "10+ years"]):
        return "Staff"
    
    # Default fallback
    return "Mid"




def _generate_template_spec(role: str, stack: List[str], level: str, suggested_assessments: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate full template specification with dependencies and file structure.
    
    Args:
        role (str): Detected role category
        stack (List[str]): Extracted technologies
        level (str): Inferred seniority level
        
    Returns:
        Dict[str, Any]: Full template specification
    """
    # Determine runtime and package manager based on stack
    runtime = "node:20-alpine"
    package_manager = "npm"
    
    if "Python" in stack:
        runtime = "python:3.11-slim"
        package_manager = "pip"
    elif "Java" in stack:
        runtime = "openjdk:17-jdk-slim"
        package_manager = "maven"
    elif "Go" in stack:
        runtime = "golang:1.21-alpine"
        package_manager = "go"
    
    # Generate dependencies based on stack
    dependencies = {}
    dev_dependencies = {}
    scripts = {}
    file_structure = {}
    
    # Skip full project templates if we're generating LeetCode-style problems
    # (LeetCode problems don't need React app structure)
    generate_full_project = not (suggested_assessments and len(suggested_assessments) > 0)
    
    # Frontend/React templates (only if NOT generating LeetCode-style problems)
    if generate_full_project and (role == "Frontend" or "React" in stack or "Vue" in stack or "Angular" in stack):
        if "React" in stack or role == "Frontend":
            dependencies = {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            }
            if "Typescript" in stack:
                dependencies["typescript"] = "^5.3.0"
                dev_dependencies = {
                    "@types/react": "^18.2.0",
                    "@types/react-dom": "^18.2.0",
                    "@types/node": "^20.10.0",
                    "vite": "^5.0.0",
                    "@vitejs/plugin-react": "^4.2.0"
                }
                scripts = {
                    "dev": "vite",
                    "build": "tsc && vite build",
                    "preview": "vite preview"
                }
                file_structure = {
                    "src/App.tsx": "// React + TypeScript starter code\nimport React from 'react';\n\nfunction App() {\n  return (\n    <div className=\"App\">\n      <h1>Assessment Project</h1>\n      {/* Your code here */}\n    </div>\n  );\n}\n\nexport default App;",
                    "src/main.tsx": "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\n\nReactDOM.createRoot(document.getElementById('root')!).render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n);",
                    "src/index.css": "body { margin: 0; font-family: sans-serif; }",
                    "index.html": "<!DOCTYPE html>\n<html>\n<head><title>Assessment</title></head>\n<body><div id=\"root\"></div></body>\n</html>",
                    "tsconfig.json": '{\n  "compilerOptions": {\n    "target": "ES2020",\n    "useDefineForClassFields": true,\n    "lib": ["ES2020", "DOM", "DOM.Iterable"],\n    "module": "ESNext",\n    "skipLibCheck": true,\n    "moduleResolution": "bundler",\n    "allowImportingTsExtensions": true,\n    "resolveJsonModule": true,\n    "isolatedModules": true,\n    "noEmit": true,\n    "jsx": "react-jsx",\n    "strict": true,\n    "noUnusedLocals": true,\n    "noUnusedParameters": true,\n    "noFallthroughCasesInSwitch": true\n  },\n  "include": ["src"]\n}',
                    "vite.config.ts": "import { defineConfig } from 'vite';\nimport react from '@vitejs/plugin-react';\n\nexport default defineConfig({\n  plugins: [react()],\n});"
                }
            else:
                dev_dependencies = {
                    "vite": "^5.0.0",
                    "@vitejs/plugin-react": "^4.2.0"
                }
                scripts = {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview"
                }
                file_structure = {
                    "src/App.jsx": "import React from 'react';\n\nfunction App() {\n  return (\n    <div className=\"App\">\n      <h1>Assessment Project</h1>\n      {/* Your code here */}\n    </div>\n  );\n}\n\nexport default App;",
                    "src/main.jsx": "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\n\nReactDOM.createRoot(document.getElementById('root')).render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n);",
                    "index.html": "<!DOCTYPE html>\n<html>\n<head><title>Assessment</title></head>\n<body><div id=\"root\"></div></body>\n</html>",
                    "vite.config.js": "import { defineConfig } from 'vite';\nimport react from '@vitejs/plugin-react';\n\nexport default defineConfig({\n  plugins: [react()],\n});"
                }
    
    # Backend/Python templates (only if NOT generating LeetCode-style problems)
    elif generate_full_project and (role == "Backend" or "Python" in stack):
        if "Django" in stack:
            dependencies = {
                "django": "^4.2.0",
                "djangorestframework": "^3.14.0"
            }
            scripts = {
                "dev": "python manage.py runserver",
                "migrate": "python manage.py migrate"
            }
            file_structure = {
                "manage.py": "# Django manage.py",
                "requirements.txt": "django==4.2.0\ndjangorestframework==3.14.0",
                "app/settings.py": "# Django settings",
                "app/urls.py": "# URL configuration"
            }
        elif "Flask" in stack:
            dependencies = {
                "flask": "^3.0.0",
                "flask-restful": "^0.3.10"
            }
            scripts = {
                "dev": "python app.py"
            }
            file_structure = {
                "app.py": "from flask import Flask\n\napp = Flask(__name__)\n\n@app.route('/')\ndef hello():\n    return 'Assessment Project'\n\nif __name__ == '__main__':\n    app.run(debug=True)",
                "requirements.txt": "flask==3.0.0\nflask-restful==0.3.10"
            }
        else:
            # Generic Python
            dependencies = {}
            scripts = {
                "dev": "python main.py"
            }
            file_structure = {
                "main.py": "# Python assessment project\n# Your code here",
                "requirements.txt": "# Add your dependencies here"
            }
    
    # Full-Stack templates (only if NOT generating LeetCode-style problems)
    elif generate_full_project and role == "Full-Stack":
        # Combine frontend and backend
        dependencies = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "express": "^4.18.0"
        }
        dev_dependencies = {
            "vite": "^5.0.0",
            "@vitejs/plugin-react": "^4.2.0"
        }
        scripts = {
            "dev": "vite",
            "server": "node server.js",
            "build": "vite build"
        }
        file_structure = {
            "src/App.jsx": "import React from 'react';\n\nfunction App() {\n  return <div>Full-Stack Assessment</div>;\n}\n\nexport default App;",
            "server.js": "const express = require('express');\nconst app = express();\n\napp.get('/api/health', (req, res) => {\n  res.json({ status: 'ok' });\n});\n\napp.listen(3000, () => console.log('Server running on port 3000'));"
        }
    
    # Generate task-specific files for LeetCode-style problems
    # If suggested_assessments provided, create individual problem files
    if suggested_assessments and len(suggested_assessments) > 0:
        tasks_dir = "problems"
        
        # Determine language based on stack
        if "Python" in stack:
            lang_ext = "py"
            test_runner = "python"
        elif "Java" in stack:
            lang_ext = "java"
            test_runner = "javac"
        elif "Typescript" in stack or "TypeScript" in stack:
            lang_ext = "ts"
            test_runner = "ts-node"
        else:
            lang_ext = "js"
            test_runner = "node"
        
        # Create main README with all problems listed
        readme_content = "# Assessment Problems\n\n"
        readme_content += f"Solve each problem in the `{tasks_dir}/` directory.\n\n"
        readme_content += "## Problems:\n\n"
        for idx, assessment in enumerate(suggested_assessments, 1):
            task_id = f"task_{idx}"
            task_title = assessment.get("title", f"Problem {idx}")
            duration = assessment.get("duration", "Not specified")
            components = assessment.get("components", [])
            readme_content += f"### Problem {idx}: {task_title}\n"
            readme_content += f"- **Duration:** {duration}\n"
            readme_content += f"- **File:** `{tasks_dir}/{task_id}.{lang_ext}`\n"
            readme_content += f"- **Test File:** `{tasks_dir}/{task_id}.test.{lang_ext}`\n"
            if components:
                readme_content += f"- **Requirements:**\n"
                for comp in components:
                    readme_content += f"  - {comp}\n"
            readme_content += "\n"
        
        readme_content += "## How to Solve:\n\n"
        readme_content += "1. Open each problem file in the `problems/` directory\n"
        readme_content += "2. Implement your solution in the provided function\n"
        readme_content += "3. Run tests using: `npm test` or `npm run test`\n"
        readme_content += "4. Submit your solution when ready\n\n"
        
        file_structure[f"{tasks_dir}/README.md"] = readme_content
        
        # Create problem files for each task
        for idx, assessment in enumerate(suggested_assessments, 1):
            task_id = f"task_{idx}"
            task_title = assessment.get("title", f"Problem {idx}")
            components = assessment.get("components", [])
            
            # Create problem file with starter code
            problem_file = f"{tasks_dir}/{task_id}.{lang_ext}"
            if lang_ext == "py":
                starter_code = f"""# Problem {idx}: {task_title}
# Duration: {assessment.get('duration', 'Not specified')}

# TODO: Implement the solution
# Requirements:
"""
                for comp in components:
                    starter_code += f"# - {comp}\n"
                starter_code += "\n# Your solution here:\n"
                starter_code += "def solution():\n    \"\"\"\n    Implement your solution here.\n    \"\"\"\n    pass\n"
                starter_code += "\n# Example usage:\n# result = solution()\n"
            elif lang_ext == "js" or lang_ext == "ts":
                starter_code = f"""// Problem {idx}: {task_title}
// Duration: {assessment.get('duration', 'Not specified')}

// TODO: Implement the solution
// Requirements:
"""
                for comp in components:
                    starter_code += f"// - {comp}\n"
                starter_code += "\n// Your solution here:\n"
                if lang_ext == "ts":
                    starter_code += "function solution(): any {\n    // Your code here\n    return null;\n}\n\nexport default solution;\n"
                else:
                    starter_code += "function solution() {\n    // Your code here\n    return null;\n}\n\nexport default solution;\n"
                starter_code += "\n// Example usage:\n// const result = solution();\n"
            elif lang_ext == "java":
                starter_code = f"""// Problem {idx}: {task_title}
// Duration: {assessment.get('duration', 'Not specified')}

// TODO: Implement the solution
// Requirements:
"""
                for comp in components:
                    starter_code += f"// - {comp}\n"
                starter_code += "\npublic class Solution {\n    public Object solution() {\n        // Your code here\n        return null;\n    }\n}\n"
            
            file_structure[problem_file] = starter_code
            
            # Create test file
            test_file = f"{tasks_dir}/{task_id}.test.{lang_ext}"
            if lang_ext == "py":
                test_code = f"""import pytest
from {task_id} import solution

def test_solution():
    # TODO: Add visible test cases
    # These tests will be shown to the candidate
    result = solution()
    assert result is not None
    # Add more test cases here
"""
            elif lang_ext == "js" or lang_ext == "ts":
                test_code = f"""import solution from './{task_id}';

describe('Problem {idx}: {task_title}', () => {{
    test('should solve the problem', () => {{
        // TODO: Add visible test cases
        // These tests will be shown to the candidate
        const result = solution();
        expect(result).toBeDefined();
        // Add more test cases here
    }});
}});
"""
            file_structure[test_file] = test_code
        
        # Add test runner script and dependencies
        if lang_ext == "py":
            scripts["test"] = "pytest problems/"
            if "pytest" not in str(dependencies):
                if not dependencies:
                    dependencies = {}
                dependencies["pytest"] = "^7.4.0"
        elif lang_ext == "js":
            scripts["test"] = "jest problems/"
            if "jest" not in str(dev_dependencies):
                if not dev_dependencies:
                    dev_dependencies = {}
                dev_dependencies["jest"] = "^29.0.0"
        elif lang_ext == "ts":
            scripts["test"] = "jest problems/"
            if "jest" not in str(dev_dependencies):
                if not dev_dependencies:
                    dev_dependencies = {}
                dev_dependencies["jest"] = "^29.0.0"
                dev_dependencies["@types/jest"] = "^29.0.0"
                dev_dependencies["ts-jest"] = "^29.0.0"
    
    # Default fallback
    if not file_structure:
        file_structure = {
            "README.md": "# Assessment Project\n\nYour assessment tasks here.",
            "package.json": "{}"
        }
    
    # Fix runtime and packageManager based on actual file structure
    # Check if we have LeetCode-style problems (problems/ directory)
    has_problems_dir = any("problems/" in k for k in file_structure.keys())
    has_react_files = any("react" in str(v).lower() or ".tsx" in k or ".jsx" in k for k, v in file_structure.items())
    has_python_files = any(".py" in k for k in file_structure.keys())
    has_java_files = any(".java" in k for k in file_structure.keys())
    has_js_ts_files = any(".js" in k or ".ts" in k for k in file_structure.keys())
    
    # For LeetCode-style problems, use WebContainer (browser runtime)
    if has_problems_dir:
        # LeetCode-style problems - always use WebContainer
        runtime = "browser"  # WebContainer runtime
        package_manager = "npm"
        # Ensure package.json exists for WebContainer
        if "package.json" not in file_structure:
            import json
            package_json = {
                "name": "assessment-problems",
                "version": "1.0.0",
                "type": "module" if has_js_ts_files else "commonjs",
                "scripts": scripts,
                "dependencies": dependencies,
                "devDependencies": dev_dependencies
            }
            file_structure["package.json"] = json.dumps(package_json, indent=2)
    elif has_react_files or (has_js_ts_files and not has_python_files and not has_java_files):
        # Frontend/Node.js - use WebContainer (browser runtime)
        runtime = "browser"  # Use browser for WebContainer
        package_manager = "npm"
    elif has_python_files:
        runtime = "python:3.11-slim"
        package_manager = "pip"
    elif has_java_files:
        runtime = "openjdk:17-jdk-slim"
        package_manager = "maven"
    else:
        # Default to WebContainer for unknown cases
        runtime = "browser"
        package_manager = "npm"
    
    # Generate template name
    stack_name = "-".join(stack[:2]).lower() if stack else "general"
    template_name = f"{role.lower()}-{stack_name}-{level.lower()}".replace(" ", "-")
    
    return {
        "name": template_name,
        "runtime": runtime,
        "packageManager": package_manager,
        "dependencies": dependencies,
        "devDependencies": dev_dependencies,
        "scripts": scripts,
        "fileStructure": file_structure
    }


def _generate_suggested_assessments(role: str, stack: List[str], level: str) -> List[Dict[str, Any]]:
    """
    Generate suggested assessments using predefined mappings and simple rules.
    
    Args:
        role (str): Detected role category
        stack (List[str]): Extracted technologies
        level (str): Inferred seniority level
        
    Returns:
        List[Dict[str, Any]]: List of assessment templates
    """
    assessments = []
    
    # Predefined mapping 1: Role-based assessments
    role_mappings = {
        "Frontend": [
            {
                "title": "React + Debugging Challenge",
                "duration": "45 min",
                "components": ["Component Build", "Bug Fixing", "Unit Tests"]
            },
            {
                "title": "UI/UX Implementation",
                "duration": "30 min", 
                "components": ["Design to Code", "Responsive Layout", "User Interaction"]
            }
        ],
        "Backend": [
            {
                "title": "API Development Challenge",
                "duration": "60 min",
                "components": ["REST API", "Database Design", "Error Handling"]
            },
            {
                "title": "System Design Lite",
                "duration": "30 min",
                "components": ["Basic Architecture", "API Flow", "State Management"]
            }
        ],
        "Data": [
            {
                "title": "Data Analysis Challenge",
                "duration": "45 min",
                "components": ["Data Processing", "Visualization", "Insights"]
            },
            {
                "title": "ML Model Building",
                "duration": "60 min",
                "components": ["Data Prep", "Model Training", "Evaluation"]
            }
        ],
        "Full-Stack": [
            {
                "title": "Full-Stack App Challenge",
                "duration": "90 min",
                "components": ["Frontend", "Backend", "Database Integration"]
            },
            {
                "title": "System Design Lite",
                "duration": "30 min",
                "components": ["Basic Architecture", "API Flow", "State Management"]
            }
        ]
    }
    
    # Predefined mapping 2: Stack-based assessments
    stack_mappings = {
        "Python": {
            "title": "Python + Django Challenge",
            "duration": "60 min",
            "components": ["API Development", "Database Design", "Testing"]
        },
        "React": {
            "title": "React + State Management",
            "duration": "45 min",
            "components": ["Component Design", "State Management", "API Integration"]
        },
        "Javascript": {
            "title": "JavaScript Fundamentals",
            "duration": "30 min",
            "components": ["ES6+ Features", "Async Programming", "DOM Manipulation"]
        }
    }
    
    # Predefined mapping 3: Level-based assessments
    level_mappings = {
        "Intern": {
            "title": "Basic Coding Challenge",
            "duration": "30 min",
            "components": ["Algorithm Basics", "Code Review", "Documentation"]
        },
        "Senior": {
            "title": "Advanced System Design",
            "duration": "75 min",
            "components": ["Architecture", "Scalability", "Performance"]
        }
    }
    
    # Rule 1: Get role-based assessments
    if role in role_mappings:
        assessments.extend(role_mappings[role])
    
    # Rule 2: Add stack-based assessment if available
    for tech in stack:
        if tech.lower() in stack_mappings:
            assessments.append(stack_mappings[tech.lower()])
            break  # Only add one stack-based assessment
    
    # Rule 3: Add level-based assessment if available
    if level in level_mappings:
        assessments.append(level_mappings[level])
    
    # Rule 4: Default assessment if no matches
    if not assessments:
        assessments.append({
            "title": "General Technical Challenge",
            "duration": "45 min",
            "components": ["Problem Solving", "Code Quality", "Documentation"]
        })
    
    # Limit to 2-3 assessments
    return assessments[:3]


