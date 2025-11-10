# MCP Server C: Watcher + Executor + Sanity Flag

## Overview
This MCP server provides real-time monitoring, code analysis, and violation detection.

## Structure
```
mcp_server_c/
├── server.py              # Main MCP server
├── agent_6_watcher.py     # Real-time violation detection
├── agent_7_executor.py    # Code analysis and pattern extraction
├── agent_8_sanity_flag.py # Risk assessment and sanity checks
├── utils/
│   └── database.py        # PostgreSQL database utilities
└── README.md
```

## Tools

1. **`watch_session(sessionId, includeFileOperations, includeTerminalEvents)`**
   - Real-time violation detection
   - Tracks file operations and terminal commands
   - Returns violations, risk scores, and alerts
   - Uses: `agent_6_watcher.py`

2. **`execute_analysis(sessionId, code)`**
   - Executes code analysis
   - Extracts patterns and quality metrics
   - Returns comprehensive analysis results
   - Uses: `agent_7_executor.py`

3. **`flag_sanity_checks(sessionId, events)`**
   - Flags suspicious behavior
   - Performs risk assessment
   - Detects anomalies and plagiarism
   - Uses: `agent_8_sanity_flag.py`

## Running

```bash
cd mcp_server_c
python server.py
```

## Environment Variables

Required:
- `BACKEND_URL` - Node.js backend URL (defaults to http://localhost:5001)

## Dependencies

- `mcp>=1.0.0`
- `requests>=2.31.0` (HTTP client for API calls)
- `python-dateutil>=2.8.0` (for date parsing)

## Database Access

**This server does NOT connect directly to the database.**

Instead, it uses HTTP API calls to the Node.js backend:
- All database operations go through `/api/mcp-database/*` endpoints
- Node.js backend handles all PostgreSQL queries
- See `utils/api_client.py` for the HTTP client implementation

## API Client

The `DatabaseAPIClient` class in `utils/api_client.py` provides methods:
- `get_interactions(session_id)` - Get all AI interactions
- `get_submissions(session_id)` - Get submissions
- `get_code_snapshots(session_id)` - Get code snapshots
- `get_file_operations(session_id)` - Get file operations
- `get_terminal_events(session_id)` - Get terminal events
- `get_interactions_by_type(session_id, event_types)` - Get by type
- `get_recent_interactions(session_id, limit)` - Get recent events
- `is_session_active(session_id)` - Check session status

