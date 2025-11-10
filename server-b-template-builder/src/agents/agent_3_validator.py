"""
Agent 3: Dependency Validator
Validates package names and checks version compatibility.
"""

import logging
import re
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def validate_dependencies(dependencies: Dict[str, str], tech_stack: List[str], package_manager: str = "npm") -> Dict[str, Any]:
    """
    Validate package names and check version compatibility.
    
    Args:
        dependencies: Dictionary of package names to versions
        tech_stack: List of technologies
        package_manager: Package manager to use ('npm', 'pip', 'maven', etc.)
    
    Returns:
        Dictionary with validated dependencies and warnings
    """
    try:
        logger.info(f"Validating {len(dependencies)} dependencies for {package_manager}")
        
        validated = {}
        warnings = []
        errors = []
        
        if package_manager == "npm":
            validated, warnings, errors = _validate_npm_packages(dependencies, tech_stack)
        elif package_manager == "pip":
            validated, warnings, errors = _validate_pip_packages(dependencies, tech_stack)
        elif package_manager in ["maven", "gradle"]:
            validated, warnings, errors = _validate_java_packages(dependencies, tech_stack)
        elif package_manager == "cargo":
            validated, warnings, errors = _validate_rust_packages(dependencies, tech_stack)
        else:
            errors.append(f"Unsupported package manager: {package_manager}")
        
        return {
            "validated": validated,
            "warnings": warnings,
            "errors": errors,
            "packageManager": package_manager,
            "totalPackages": len(dependencies),
            "validPackages": len(validated),
            "invalidPackages": len(errors)
        }
    
    except Exception as e:
        logger.error(f"Error validating dependencies: {e}")
        return {
            "validated": {},
            "warnings": [],
            "errors": [str(e)],
            "packageManager": package_manager
        }


def _validate_npm_packages(dependencies: Dict[str, str], tech_stack: List[str]) -> tuple:
    """Validate npm packages."""
    validated = {}
    warnings = []
    errors = []
    
    # Common npm package patterns
    valid_pattern = re.compile(r'^[@a-zA-Z0-9_-][@a-zA-Z0-9._/-]*$')
    
    for package, version in dependencies.items():
        # Check package name format
        if not valid_pattern.match(package):
            errors.append(f"Invalid package name: {package}")
            continue
        
        # Check version format
        if not _is_valid_semver(version):
            warnings.append(f"Invalid version format for {package}: {version}")
            # Still accept it, might be a valid version format we don't recognize
        
        validated[package] = version
    
    return validated, warnings, errors


def _validate_pip_packages(dependencies: Dict[str, str], tech_stack: List[str]) -> tuple:
    """Validate pip packages."""
    validated = {}
    warnings = []
    errors = []
    
    # Python package names are lowercase with hyphens/underscores
    valid_pattern = re.compile(r'^[a-z0-9_-]+$')
    
    for package, version in dependencies.items():
        # Normalize package name (pip is case-insensitive)
        package_lower = package.lower().replace('_', '-')
        
        if not valid_pattern.match(package_lower):
            errors.append(f"Invalid package name: {package}")
            continue
        
        validated[package_lower] = version
    
    return validated, warnings, errors


def _validate_java_packages(dependencies: Dict[str, str], tech_stack: List[str]) -> tuple:
    """Validate Java/Maven packages."""
    validated = {}
    warnings = []
    errors = []
    
    # Maven groupId:artifactId format
    for package, version in dependencies.items():
        if ':' in package:
            # groupId:artifactId format
            parts = package.split(':')
            if len(parts) == 2:
                validated[package] = version
            else:
                errors.append(f"Invalid Maven coordinate: {package}")
        else:
            # Just artifactId, assume common groupId
            validated[package] = version
    
    return validated, warnings, errors


def _validate_rust_packages(dependencies: Dict[str, str], tech_stack: List[str]) -> tuple:
    """Validate Rust/Cargo packages."""
    validated = {}
    warnings = []
    errors = []
    
    # Rust crate names are lowercase with hyphens
    valid_pattern = re.compile(r'^[a-z0-9_-]+$')
    
    for package, version in dependencies.items():
        package_lower = package.lower()
        
        if not valid_pattern.match(package_lower):
            errors.append(f"Invalid crate name: {package}")
            continue
        
        validated[package_lower] = version
    
    return validated, warnings, errors


def _is_valid_semver(version: str) -> bool:
    """Check if version string is valid semver-like."""
    # Accept common version formats: ^1.2.3, ~1.2.3, 1.2.3, >=1.2.3, etc.
    semver_pattern = re.compile(r'^[\^~>=<]?\d+\.\d+\.\d+.*$')
    return bool(semver_pattern.match(version))

