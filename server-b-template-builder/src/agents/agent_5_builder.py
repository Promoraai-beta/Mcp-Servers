"""
Agent 5: WebContainer Structure Builder
Organizes files into complete folder structure, creates package.json, README, configs.

Now uses the ProjectGenerator to create realistic, role-based projects with intentional issues.
"""

import json
import logging
from typing import Dict, List, Any, Optional

# Import React app builder
try:
    from agent_5_react_app_builder import build_react_app_with_bugs
except ImportError:
    build_react_app_with_bugs = None

# Import project generator
try:
    from agent_5_project_generator import ProjectGenerator
except ImportError:
    ProjectGenerator = None

logger = logging.getLogger(__name__)


def build_webcontainer_structure(
    tasks: List[Dict[str, Any]],
    problems: Dict[str, str],
    validated_deps: Dict[str, Any],
    tech_stack: List[str],
    language: str = "javascript",
    job_role: Optional[str] = None,
    experience_level: Optional[str] = None,
    skills_to_test: Optional[List[str]] = None,
    problem_types: Optional[List[str]] = None,
    complexity: str = "medium"
) -> Dict[str, Any]:
    """
    Build complete WebContainer file structure.
    
    Now supports role-based project generation with intentional issues.
    
    Args:
        tasks: Assessment tasks
        problems: Generated problem files from agent_4 (legacy, may not be used)
        validated_deps: Validated dependencies from agent_3
        tech_stack: List of technologies
        language: Programming language
        job_role: Job role (e.g., "Frontend Developer")
        experience_level: Experience level (e.g., "Mid-level")
        skills_to_test: Skills to assess (e.g., ["Performance", "Accessibility"])
        problem_types: Types of problems (e.g., ["bugs", "optimization"])
        complexity: "easy", "medium", "hard"
    
    Returns:
        Complete fileStructure ready for WebContainer with metadata
    """
    try:
        logger.info(f"Building WebContainer structure for {len(tasks)} tasks")
        
        # Try to use tool-based ProjectGenerator if role information is available
        # This uses LLM and MCP tools to generate realistic projects
        if job_role:
            try:
                # Tool-based generator was removed - using template-based approach
                # from agent_5_builder_with_tools import build_project_with_tools
                logger.info(f"Using template-based ProjectGenerator for role: {job_role}")
                project_result = None  # Will fall back to template generator below
                
                # Extract skills and problem types from tasks if not provided
                if not skills_to_test:
                    skills_to_test = _extract_skills_from_tasks(tasks, tech_stack)
                if not problem_types:
                    problem_types = _extract_problem_types_from_tasks(tasks)
                if not experience_level:
                    experience_level = "Mid-level"  # Default
                
                # Get job description from tasks if available
                job_description = None
                if tasks and len(tasks) > 0:
                    # Try to extract context from first task
                    first_task = tasks[0]
                    job_description = first_task.get("description", "") or first_task.get("context", "")
                
                # Generate project using tools (LLM, agents, etc.)
                project_result = build_project_with_tools(
                    job_role=job_role,
                    experience_level=experience_level,
                    tech_stack=tech_stack,
                    assessment_tasks=tasks,
                    job_description=job_description,
                    skills_to_test=skills_to_test,
                    problem_types=problem_types,
                    complexity=complexity
                )
                
            except ImportError:
                logger.warning("Tool-based generator not available, using template-based generator")
                # Fall back to template-based generator
                if ProjectGenerator:
                    generator = ProjectGenerator()
                    
                    if not skills_to_test:
                        skills_to_test = _extract_skills_from_tasks(tasks, tech_stack)
                    if not problem_types:
                        problem_types = _extract_problem_types_from_tasks(tasks)
                    if not experience_level:
                        experience_level = "Mid-level"
                    
                    project_result = generator.generate_project(
                        job_role=job_role,
                        experience_level=experience_level,
                        tech_stack=tech_stack,
                        skills_to_test=skills_to_test,
                        problem_types=problem_types,
                        complexity=complexity,
                        estimated_time=45
                    )
                else:
                    project_result = None
            except Exception as e:
                logger.error(f"Error using tool-based generator: {e}, falling back to template")
                # Fall back to template-based
                if ProjectGenerator:
                    generator = ProjectGenerator()
                    if not skills_to_test:
                        skills_to_test = _extract_skills_from_tasks(tasks, tech_stack)
                    if not problem_types:
                        problem_types = _extract_problem_types_from_tasks(tasks)
                    project_result = generator.generate_project(
                        job_role=job_role,
                        experience_level=experience_level or "Mid-level",
                        tech_stack=tech_stack,
                        skills_to_test=skills_to_test,
                        problem_types=problem_types,
                        complexity=complexity,
                        estimated_time=45
                    )
                else:
                    project_result = None
            
            if project_result:
                file_structure = project_result["projectStructure"]
            
            # Extract metadata
            if "package.json" in file_structure:
                try:
                    package_json = json.loads(file_structure["package.json"])
                    dependencies = package_json.get("dependencies", {})
                    dev_dependencies = package_json.get("devDependencies", {})
                    scripts = package_json.get("scripts", {})
                except:
                    dependencies = {}
                    dev_dependencies = {}
                    scripts = {}
            else:
                dependencies = {}
                dev_dependencies = {}
                scripts = {}
            
            # Determine runtime and package manager
            package_manager = "npm"
            runtime = "browser"
            lang_ext = "jsx" if language == "javascript" else "tsx"
            
            # Build enhanced template spec with issue metadata
            template_spec = {
                "name": f"assessment-{language}",
                "runtime": runtime,
                "packageManager": package_manager,
                "dependencies": dependencies,
                "devDependencies": dev_dependencies,
                "scripts": scripts,
                "fileStructure": file_structure,
                # Include project metadata
                "projectMetadata": project_result.get("projectMetadata", {}),
                "intentionalIssues": project_result.get("intentionalIssues", []),
                "evaluationCriteria": project_result.get("evaluationCriteria", {}),
                "candidateInstructions": project_result.get("candidateInstructions", ""),
                "setupInstructions": project_result.get("setupInstructions", "")
            }
            
            logger.info(f"Built role-based project with {len(file_structure)} files and {len(project_result.get('intentionalIssues', []))} issues")
            return template_spec
        
        # Fallback to legacy behavior for backwards compatibility
        logger.info("Using legacy project generation")
        
        # Check if this is a React debugging challenge
        is_react_debug = _is_react_debugging_challenge(tasks, tech_stack, language)
        
        file_structure = {}
        
        # If it's a React debugging challenge, build full React app with bugs
        if is_react_debug and build_react_app_with_bugs:
            logger.info("Detected React debugging challenge - building full React app with bugs")
            react_app_files = build_react_app_with_bugs(
                tasks,
                tech_stack,
                use_typescript=(language == "typescript")
            )
            file_structure.update(react_app_files)
            # React app already includes package.json, so we're done
            # Extract metadata from the React app structure
            lang_ext = "tsx" if language == "typescript" else "jsx"
            package_manager = "npm"
            runtime = "browser"
            
            # Extract dependencies from package.json if it exists
            if "package.json" in file_structure:
                try:
                    package_json = json.loads(file_structure["package.json"])
                    dependencies = package_json.get("dependencies", {})
                    dev_dependencies = package_json.get("devDependencies", {})
                    scripts = package_json.get("scripts", {})
                except:
                    dependencies = {}
                    dev_dependencies = {}
                    scripts = {}
            else:
                dependencies = {}
                dev_dependencies = {}
                scripts = {}
        else:
            # Start with generated problems (LeetCode-style)
            file_structure.update(problems)
            
            # Determine file extension and package manager
            lang_ext = {
                "javascript": "js",
                "typescript": "ts",
                "python": "py",
                "java": "java"
            }.get(language.lower(), "js")
            
            package_manager = "npm" if language in ["javascript", "typescript"] else "pip"
            
            # Extract dependencies and scripts
            dependencies = validated_deps.get("validated", {})
            warnings = validated_deps.get("warnings", [])
            
            # Build scripts based on language and package manager
            scripts = {}
            dev_dependencies = {}
            
            # Only add test scripts for npm-based projects (JavaScript/TypeScript)
            # For Python projects, tests should be run via requirements.txt and pip, not npm
            if package_manager == "npm" and lang_ext in ["js", "ts"]:
                # For JavaScript/TypeScript projects, use Jest
                scripts["test"] = "jest problems/"
                if "jest" not in dev_dependencies:
                    dev_dependencies["jest"] = "^29.0.0"
                if lang_ext == "ts":
                    dev_dependencies["@types/jest"] = "^29.0.0"
                    dev_dependencies["ts-jest"] = "^29.0.0"
            elif package_manager == "npm" and lang_ext == "py":
                # Python project in WebContainer - still use npm but run Python test command
                # Note: pytest must be installed via pip/requirements.txt first
                scripts["test"] = "python3 -m pytest problems/ || echo 'Note: Install pytest first: pip install pytest'"
                # Don't add pytest to npm dependencies - it should be in requirements.txt
            elif package_manager == "pip":
                # Pure Python project - no package.json needed, but if we create one for WebContainer
                # use a Python command
                scripts["test"] = "python3 -m pytest problems/ || echo 'Note: Install pytest first: pip install pytest'"
            else:
                # Default: no test script if package manager not recognized
                scripts["test"] = "echo 'No test runner configured'"
            
            # Clean up dependencies - remove pytest from npm dependencies if it exists
            # (pytest should only be in requirements.txt for Python projects)
            if package_manager == "npm" and "pytest" in dependencies:
                logger.warning("Removing pytest from npm dependencies (should be in requirements.txt for Python projects)")
                dependencies.pop("pytest", None)
            
            # Create package.json only for npm-based projects
            # For Python projects, we might still create package.json for WebContainer setup
            # but with minimal content
            package_json = {
                "name": "assessment-problems",
                "version": "1.0.0",
                "type": "module" if lang_ext in ["js", "ts"] else "commonjs",
                "scripts": scripts,
                "dependencies": dependencies,
                "devDependencies": dev_dependencies
            }
            
            file_structure["package.json"] = json.dumps(package_json, indent=2)
        
        # Create requirements.txt if Python files are present (even if package manager is npm)
        # Check if there are any Python files in the structure
        has_python_files = any(
            key.endswith(".py") or "/" in key and key.split("/")[-1].endswith(".py")
            for key in file_structure.keys()
        )
        
        if has_python_files or lang_ext == "py":
            # Generate requirements.txt for Python dependencies
            python_deps = []
            
            # Add pytest if test script uses it
            if "pytest" in scripts.get("test", ""):
                python_deps.append("pytest==7.4.0")
            
            # Add any other Python dependencies from validated_deps
            # Note: This assumes validated_deps might contain Python packages
            # In practice, you might want to separate Python and npm dependencies
            
            if python_deps:
                file_structure["requirements.txt"] = "\n".join(python_deps) + "\n"
                logger.info(f"Created requirements.txt with {len(python_deps)} Python dependencies")
        
        # Create TypeScript config if needed (only for LeetCode-style problems, not React apps)
        if lang_ext == "ts" and not is_react_debug:
            tsconfig = {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "ESNext",
                    "lib": ["ES2020", "DOM"],
                    "moduleResolution": "node",
                    "strict": True,
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                    "forceConsistentCasingInFileNames": True,
                    "resolveJsonModule": True
                },
                "include": ["problems/**/*"],
                "exclude": ["node_modules"]
            }
            file_structure["tsconfig.json"] = json.dumps(tsconfig, indent=2)
        
        # Create Jest config if needed (only for LeetCode-style problems, not React apps)
        if lang_ext in ["js", "ts"] and not is_react_debug:
            jest_config = {
                "preset": "ts-jest" if lang_ext == "ts" else "default",
                "testEnvironment": "node",
                "roots": ["<rootDir>/problems"],
                "testMatch": ["**/*.test.ts", "**/*.test.js"]
            }
            file_structure["jest.config.json"] = json.dumps(jest_config, indent=2)
        
        # Determine runtime for template spec
        if not is_react_debug:
            # For LeetCode-style problems
            has_problems_dir = any("problems/" in k for k in file_structure.keys())
            runtime = "browser" if has_problems_dir else "node"
        # else: runtime already set to "browser" for React apps
        
        # Build template spec
        template_spec = {
            "name": f"assessment-{language}",
            "runtime": runtime,
            "packageManager": package_manager,
            "dependencies": dependencies,
            "devDependencies": dev_dependencies,
            "scripts": scripts,
            "fileStructure": file_structure
        }
        
        logger.info(f"Built WebContainer structure with {len(file_structure)} files")
        return template_spec
    
    except Exception as e:
        logger.error(f"Error building WebContainer structure: {e}")
        return {
            "fileStructure": {},
            "runtime": "browser",
            "packageManager": "npm"
        }


def _is_react_debugging_challenge(
    tasks: List[Dict[str, Any]],
    tech_stack: List[str],
    language: str
) -> bool:
    """
    Determine if this is a React debugging challenge that needs a full app.
    
    Args:
        tasks: Assessment tasks
        tech_stack: List of technologies
        language: Programming language
    
    Returns:
        True if this should be a full React app with bugs
    """
    # Check if React is in tech stack
    has_react = any("react" in str(t).lower() for t in tech_stack)
    
    # Check if language is JavaScript/TypeScript
    is_js_lang = language.lower() in ["javascript", "typescript", "js", "ts"]
    
    # Check if any task mentions debugging, bugs, or React
    has_debug_task = any(
        "debug" in task.get("title", "").lower() or
        "react" in task.get("title", "").lower() or
        any("bug" in str(c).lower() or "debug" in str(c).lower() 
            for c in task.get("components", []))
        for task in tasks
    )
    
    return (has_react or has_debug_task) and is_js_lang


def _extract_skills_from_tasks(tasks: List[Dict[str, Any]], tech_stack: List[str]) -> List[str]:
    """Extract skills to test from tasks and tech stack."""
    skills = []
    
    # Common skill mappings
    skill_keywords = {
        "performance": ["performance", "optimization", "speed", "fast"],
        "accessibility": ["accessibility", "a11y", "aria", "screen reader"],
        "responsive": ["responsive", "mobile", "layout", "breakpoint"],
        "state": ["state", "redux", "context", "state management"],
        "api": ["api", "fetch", "axios", "rest", "graphql"],
        "testing": ["test", "testing", "jest", "cypress"],
        "security": ["security", "xss", "csrf", "authentication"]
    }
    
    # Check tasks for skill mentions
    for task in tasks:
        title = task.get("title", "").lower()
        components = [str(c).lower() for c in task.get("components", [])]
        description = task.get("description", "").lower()
        
        combined_text = f"{title} {' '.join(components)} {description}"
        
        for skill, keywords in skill_keywords.items():
            if any(kw in combined_text for kw in keywords):
                if skill not in skills:
                    skills.append(skill.capitalize())
    
    # If no skills found, add defaults based on tech stack
    if not skills:
        if "React" in str(tech_stack):
            skills = ["Performance", "Accessibility"]
        else:
            skills = ["Code Quality", "Best Practices"]
    
    return skills


def _extract_problem_types_from_tasks(tasks: List[Dict[str, Any]]) -> List[str]:
    """Extract problem types from tasks."""
    problem_types = []
    
    type_keywords = {
        "bugs": ["bug", "fix", "broken", "error", "issue"],
        "performance": ["performance", "slow", "optimization", "optimize"],
        "security": ["security", "vulnerability", "xss", "csrf"],
        "accessibility": ["accessibility", "a11y", "aria"],
        "optimization": ["optimize", "performance", "speed"],
        "refactoring": ["refactor", "clean", "improve", "quality"],
        "error_handling": ["error", "exception", "handling"],
        "ux": ["ux", "user experience", "ui", "interface"]
    }
    
    for task in tasks:
        title = task.get("title", "").lower()
        components = [str(c).lower() for c in task.get("components", [])]
        description = task.get("description", "").lower()
        
        combined_text = f"{title} {' '.join(components)} {description}"
        
        for ptype, keywords in type_keywords.items():
            if any(kw in combined_text for kw in keywords):
                if ptype not in problem_types:
                    problem_types.append(ptype)
    
    # Default to bugs if nothing found
    if not problem_types:
        problem_types = ["bugs", "optimization"]
    
    return problem_types

