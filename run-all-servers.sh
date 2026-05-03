#!/bin/bash

# Script to run all MCP servers
# This will start all three MCP servers in separate background processes

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚀 Starting all MCP servers...${NC}"
echo ""

# Function to check if a process is running
check_process() {
    if pgrep -f "$1" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to start a server
start_server() {
    local server_name=$1
    local server_dir=$2
    local server_script=$3
    
    echo -e "${YELLOW}Starting ${server_name}...${NC}"
    
    cd "$SCRIPT_DIR/$server_dir"
    
    # Determine Python executable (use venv if available)
    local python_exec="python3"
    if [ -d "venv" ]; then
        python_exec="venv/bin/python"
    fi
    
    # Run with nohup - MCP servers will wait for stdio connections
    # They communicate via stdio, so they'll stay alive waiting for MCP protocol messages
    # stdin is kept open by nohup, and servers will wait for proper JSON-RPC messages
    nohup $python_exec "$server_script" < /dev/null > "/tmp/mcp-${server_name}.log" 2>&1 &
    
    local pid=$!
    echo $pid > "/tmp/mcp-${server_name}.pid"
    echo -e "${GREEN}✅ ${server_name} started (PID: $pid)${NC}"
    echo -e "   Logs: /tmp/mcp-${server_name}.log"
    echo -e "   ${YELLOW}Note: MCP servers wait for stdio connections. They'll be ready when the backend connects.${NC}"
    
    cd "$SCRIPT_DIR"
    sleep 2
}

# Start Server A (Job Analysis)
if [ -d "server-a-job-analysis" ]; then
    start_server "server-a" "server-a-job-analysis" "src/server.py"
else
    echo -e "${RED}❌ server-a-job-analysis not found${NC}"
fi

# Start Server B (Template Builder)
if [ -d "server-b-template-builder" ]; then
    start_server "server-b" "server-b-template-builder" "src/server.py"
else
    echo -e "${RED}❌ server-b-template-builder not found${NC}"
fi

# Start Server C (Monitoring — Python/stdio)
if [ -d "server-c-monitoring" ]; then
    start_server "server-c-monitoring" "server-c-monitoring" "src/server.py"
else
    echo -e "${RED}❌ server-c-monitoring not found${NC}"
fi

# Start Server C (Orchestrator — Node.js/HTTP on port 3002)
if [ -d "server-c-orchestrator" ]; then
    echo -e "${YELLOW}Starting server-c-orchestrator...${NC}"
    cd "$SCRIPT_DIR/server-c-orchestrator"
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing npm dependencies...${NC}"
        npm install --silent
    fi
    export $(grep -v '^#' .env | xargs) 2>/dev/null || true
    nohup npx ts-node src/server.ts > "/tmp/mcp-server-c-orchestrator.log" 2>&1 &
    local pid=$!
    echo $pid > "/tmp/mcp-server-c-orchestrator.pid"
    echo -e "${GREEN}✅ server-c-orchestrator started (PID: $pid)${NC}"
    echo -e "   Logs: /tmp/mcp-server-c-orchestrator.log"
    cd "$SCRIPT_DIR"
    sleep 2
else
    echo -e "${RED}❌ server-c-orchestrator not found${NC}"
fi

echo ""
echo -e "${GREEN}✅ All MCP servers started!${NC}"
echo ""
echo "To view logs:"
echo "  tail -f /tmp/mcp-server-a.log"
echo "  tail -f /tmp/mcp-server-b.log"
echo "  tail -f /tmp/mcp-server-c-monitoring.log"
echo "  tail -f /tmp/mcp-server-c-orchestrator.log"
echo ""
echo "Server C Orchestrator runs on port 3002 (HTTP REST)."
echo ""
echo "To stop all servers:"
echo "  ./stop-all-servers.sh"
echo ""
echo "Or manually:"
echo "  kill \$(cat /tmp/mcp-server-a.pid)"
echo "  kill \$(cat /tmp/mcp-server-b.pid)"
echo "  kill \$(cat /tmp/mcp-server-c-monitoring.pid)"
echo "  kill \$(cat /tmp/mcp-server-c-orchestrator.pid)"

