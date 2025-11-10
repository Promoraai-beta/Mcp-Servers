import json
import os
from typing import Any

# Static resource registry
RESOURCES = [
    {
        "uri": "promora://templates/react-vite",
        "name": "React Vite Template",
        "description": "Base React + Vite template skeleton",
        "mimeType": "application/json",
    },
    {
        "uri": "promora://templates/python-flask",
        "name": "Python Flask Template",
        "description": "Base Flask app template",
        "mimeType": "application/json",
    },
    {
        "uri": "promora://bugs/common",
        "name": "Common Bug Patterns",
        "description": "Common intentional issues for seeding projects",
        "mimeType": "application/json",
    },
]


async def read_resource(uri: str) -> Any:
    base = os.path.join(os.path.dirname(__file__), "templates")
    if uri == "promora://templates/react-vite":
        path = os.path.join(base, "react_vite.json")
    elif uri == "promora://templates/python-flask":
        path = os.path.join(base, "python_flask.json")
    elif uri == "promora://bugs/common":
        path = os.path.join(base, "bugs.json")
    else:
        raise ValueError(f"Unknown resource: {uri}")

    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
