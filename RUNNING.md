# Running MCP Servers

## Quick Start

### Start All Servers
```bash
cd mcp-servers
./run-all-servers.sh
```

### Stop All Servers
```bash
cd mcp-servers
./stop-all-servers.sh
```

### Test Servers
```bash
cd mcp-servers
python3 test-mcp-servers.py
```

## Server Details

### Server A - Job Analysis
- **Path**: `server-a-job-analysis/src/server.py`
- **Purpose**: Job posting verification, assessment generation
- **Tools**: 
  - `verify_job_posting`
  - `generate_assessments`
  - `analyze_job_pipeline`

### Server B - Template Builder
- **Path**: `server-b-template-builder/src/server.py`
- **Purpose**: Dependency validation, LeetCode problem generation, project building
- **Tools**:
  - `validate_dependencies`
  - `generate_leetcode_problems`
  - `build_webcontainer_structure`

### Server C - Monitoring
- **Path**: `server-c-monitoring/src/server.py`
- **Purpose**: Real-time monitoring, code analysis, violation detection
- **Tools**:
  - `watch_session`
  - `execute_analysis`
  - `flag_sanity_checks`

## How It Works

MCP servers communicate using the **Model Context Protocol** over stdio (standard input/output). They:

1. Wait for JSON-RPC messages on stdin
2. Process requests and send responses on stdout
3. Log errors and info to stderr

## Integration with Backend

The Node.js backend automatically spawns these servers as child processes when needed. The backend MCP client (`backend/src/mcp/client.ts`) handles:

- Process spawning with stdio pipes
- MCP protocol initialization
- Tool discovery and calling
- Lifecycle management

## Manual Testing

### View Logs
```bash
# Real-time logs
tail -f /tmp/mcp-server-a.log
tail -f /tmp/mcp-server-b.log
tail -f /tmp/mcp-server-c.log

# All logs at once
tail -f /tmp/mcp-server-*.log
```

### Check Running Status
```bash
# Check PIDs
cat /tmp/mcp-server-a.pid
cat /tmp/mcp-server-b.pid
cat /tmp/mcp-server-c.pid

# Check processes
ps aux | grep server.py | grep -v grep
```

### Test with Python Script
```bash
python3 test-mcp-servers.py
```

This will:
- Connect to each server
- Send initialization requests
- List available tools
- Verify servers are responding correctly

## Troubleshooting

### Servers Not Starting
1. Check dependencies are installed: `./install-dependencies.sh`
2. Verify Python 3 is available: `python3 --version`
3. Check virtual environments exist in each server directory
4. Review logs: `cat /tmp/mcp-server-*.log`

### Servers Exit Immediately
MCP servers communicate over stdio and need an active connection. They're designed to:
- Be spawned by the backend (automatic)
- Run with an MCP client (manual testing)
- Stay alive waiting for MCP protocol messages

If they exit, check:
- Virtual environment activation
- Python dependencies (especially `mcp` package)
- Server script permissions

### Connection Issues
- Ensure servers are running: `ps aux | grep server.py`
- Check backend logs for connection errors
- Verify server paths in backend configuration
- Test with `test-mcp-servers.py`

## Notes

- Servers run in the background when started with `run-all-servers.sh`
- Logs are written to `/tmp/mcp-server-{name}.log`
- PID files are stored in `/tmp/mcp-server-{name}.pid`
- Servers use virtual environments if available, otherwise system Python 3





