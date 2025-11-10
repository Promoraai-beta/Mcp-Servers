# MCP Servers

This directory contains the three MCP (Model Context Protocol) servers that power the assessment platform.

## Structure

```
mcp-servers/
├── server-a-job-analysis/        # Job Analysis + Assessment Generation
├── server-b-template-builder/    # Template Building + Project Generation
└── server-c-monitoring/          # Real-time Monitoring + Code Analysis
```

## Installation

Install dependencies for all servers:

```bash
./install-dependencies.sh
```

Or install for each server individually:

```bash
cd server-a-job-analysis
pip install -r requirements.txt
```

## Running Servers

Servers are automatically spawned by the Node.js backend as child processes. They communicate via stdio using the MCP protocol.

You can also test servers manually:

```bash
# Server A
cd server-a-job-analysis
python3 src/server.py

# Server B
cd server-b-template-builder
python3 src/server.py

# Server C
cd server-c-monitoring
python3 src/server.py
```

## Architecture

Each server:
- Uses **true MCP protocol** (JSON-RPC over stdio)
- Contains agents in `src/agents/`
- Main server file: `src/server.py`
- Dependencies: `requirements.txt`

## Development

Each server is independent and can be developed separately. They expose tools via the MCP protocol that the backend consumes.

