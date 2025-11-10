"""
API Client for MCP Server C
Makes HTTP requests to Node.js backend for database operations.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class DatabaseAPIClient:
    """HTTP client for database operations via Node.js backend."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the backend API (defaults to BACKEND_URL env var or http://localhost:5001)
        """
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://localhost:5001")
        self.api_path = "/api/mcp-database"
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Make HTTP GET request to backend API."""
        url = f"{self.base_url}{self.api_path}{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"API request failed: {url} - {e}")
            return []
    
    def get_interactions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all AI interactions for a session."""
        return self._make_request(f"/interactions/{session_id}")
    
    def get_submissions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get submissions for a session."""
        return self._make_request(f"/submissions/{session_id}")
    
    def get_code_snapshots(self, session_id: str) -> List[Dict[str, Any]]:
        """Get code snapshots for a session."""
        return self._make_request(f"/code-snapshots/{session_id}")
    
    def get_file_operations(self, session_id: str) -> List[Dict[str, Any]]:
        """Get file operations for a session."""
        return self._make_request(f"/file-operations/{session_id}")
    
    def get_terminal_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Get terminal events for a session."""
        return self._make_request(f"/terminal-events/{session_id}")
    
    def get_interactions_by_type(self, session_id: str, event_types: List[str]) -> List[Dict[str, Any]]:
        """Get interactions by event type."""
        params = {"eventTypes": ",".join(event_types)}
        return self._make_request(f"/interactions-by-type/{session_id}", params)
    
    def get_recent_interactions(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent interactions (last N events)."""
        params = {"limit": limit}
        return self._make_request(f"/recent-interactions/{session_id}", params)
    
    def is_session_active(self, session_id: str) -> bool:
        """Check if session is active."""
        try:
            url = f"{self.base_url}{self.api_path}/session-status/{session_id}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get("isActive", False)
        except RequestException as e:
            logger.error(f"Failed to check session status: {e}")
            return False

