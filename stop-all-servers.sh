#!/bin/bash

# Script to stop all MCP servers

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping all MCP servers...${NC}"
echo ""

# Function to stop a server
stop_server() {
    local server_name=$1
    local pid_file="/tmp/mcp-${server_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill "$pid" 2>/dev/null; then
            echo -e "${GREEN}✅ Stopped ${server_name} (PID: $pid)${NC}"
            rm -f "$pid_file"
        else
            echo -e "${RED}❌ Failed to stop ${server_name} (process may not be running)${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "${YELLOW}⚠️  ${server_name} PID file not found (may not be running)${NC}"
    fi
}

# Stop all servers
stop_server "server-a"
stop_server "server-b"
stop_server "server-c"

# Also try to kill by process name as fallback
pkill -f "server-a-job-analysis/src/server.py" 2>/dev/null
pkill -f "server-b-template-builder/src/server.py" 2>/dev/null
pkill -f "server-c-monitoring/src/server.py" 2>/dev/null

echo ""
echo -e "${GREEN}✅ Done!${NC}"





