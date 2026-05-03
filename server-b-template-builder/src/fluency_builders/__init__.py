"""Role-specific AI fluency simulation builders."""

from .frontend_builder import FrontendFluencyBuilder
from .backend_builder import BackendFluencyBuilder
from .analyst_builder import AnalystFluencyBuilder


def get_fluency_builder(role_id: str):
    """Get the appropriate builder for a role."""
    builders = {
        "frontend": FrontendFluencyBuilder,
        "backend": BackendFluencyBuilder,
        "analyst": AnalystFluencyBuilder,
    }
    cls = builders.get(role_id)
    return cls() if cls else None
