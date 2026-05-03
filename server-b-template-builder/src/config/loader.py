"""
Role simulation config loader.
Resolves job role strings to canonical role IDs and loads simulation config.
"""

import json
import os
from typing import Dict, Any, Optional

_CONFIG: Optional[Dict[str, Any]] = None


def _get_config_path() -> str:
    """Get path to role_simulation_config.json."""
    return os.path.join(os.path.dirname(__file__), "role_simulation_config.json")


def load_role_config() -> Dict[str, Any]:
    """Load role simulation config from JSON. Cached after first load."""
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG
    path = _get_config_path()
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        _CONFIG = json.load(f)
    return _CONFIG


def resolve_role(job_role: Optional[str]) -> Optional[str]:
    """
    Resolve a job role string to a canonical role ID (frontend, backend, analyst).
    Returns None if no match.
    """
    if not job_role or not isinstance(job_role, str):
        return None
    role_lower = job_role.strip().lower()
    config = load_role_config()
    for role_id, role_data in config.items():
        aliases = role_data.get("aliases", [])
        if role_lower == role_id.lower():
            return role_id
        if any(role_lower == str(a).lower() for a in aliases):
            return role_id
        if any(role_lower in str(a).lower() for a in aliases):
            return role_id
    return None


def get_simulation_config(role_id: str) -> Optional[Dict[str, Any]]:
    """Get full simulation config for a role."""
    config = load_role_config()
    return config.get(role_id)
