#!/bin/bash

# Production startup script for MCP servers
# This script ensures proper environment setup and error handling

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚀 Starting MCP Servers (Production Mode)...${NC}"
echo ""

# Function to check if .env file exists and has required keys
check_env_file() {
    local server_dir=$1
    local env_file="$SCRIPT_DIR/$server_dir/.env"

    if [ ! -f "$env_file" ]; then
        echo -e "${YELLOW}⚠️  Warning: $server_dir/.env not found${NC}"
        return 1
    fi

    # Check for required keys based on server
    if [[ "$server_dir" == *"server-a"* ]] || [[ "$server_dir" == *"server-b"* ]] || [[ "$server_dir" == *"server-c-orchestrator"* ]]; then
        if ! grep -q "OPENAI_API_KEY" "$env_file" || grep -q "OPENAI_API_KEY=your-azure-key-here" "$env_file"; then
            echo -e "${YELLOW}⚠️  Warning: $server_dir/.env has placeholder OPENAI_API_KEY${NC}"
            echo -e "${YELLOW}   Please update with your actual Azure API key${NC}"
        fi
    fi

    return 0
}

# Function to start a server with proper error handling
start_server() {
    local server_name=$1
    local server_dir=$2
    local server_script=$3
    
    echo -e "${YELLOW}Starting ${server_name}...${NC}"
    
    # Check if server directory exists
    if [ ! -d "$SCRIPT_DIR/$server_dir" ]; then
        echo -e "${RED}❌ $server_dir not found${NC}"
        return 1
    fi
    
    cd "$SCRIPT_DIR/$server_dir"
    
    # Check if .env exists
    if ! check_env_file "$server_dir"; then
        echo -e "${RED}❌ $server_dir/.env is missing or incomplete${NC}"
        return 1
    fi
    
    # Determine Python executable
    local python_exec="python3"
    if [ -d "venv" ]; then
        python_exec="venv/bin/python"
        
        # Check if venv Python exists
        if [ ! -f "$python_exec" ]; then
            echo -e "${YELLOW}Creating virtual environment...${NC}"
            python3 -m venv venv
            python_exec="venv/bin/python"
        fi
        
        # Install/update dependencies
        echo -e "${YELLOW}Installing dependencies...${NC}"
        "$python_exec" -m pip install --quiet --upgrade pip > /dev/null 2>&1
        if [ -f "requirements.txt" ]; then
            "$python_exec" -m pip install --quiet -r requirements.txt > /dev/null 2>&1
        fi
    else
        echo -e "${YELLOW}No venv found, using system Python${NC}"
    fi
    
    # Check if server script exists
    if [ ! -f "$server_script" ]; then
        echo -e "${RED}❌ $server_script not found${NC}"
        return 1
    fi
    
    # Kill existing process if running
    if [ -f "/tmp/mcp-${server_name}.pid" ]; then
        local old_pid=$(cat "/tmp/mcp-${server_name}.pid" 2>/dev/null || echo "")
        if [ ! -z "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
            echo -e "${YELLOW}Stopping existing ${server_name} (PID: $old_pid)...${NC}"
            kill "$old_pid" 2>/dev/null || true
            sleep 1
        fi
    fi
    
    # Start server with proper logging
    local log_file="/tmp/mcp-${server_name}.log"
    echo -e "${BLUE}Starting ${server_name}...${NC}"
    
    # Load environment variables from .env file
    # set -a exports every variable that gets assigned; source reads the file;
    # set +a restores the default. This handles hyphens, spaces, and special chars safely.
    if [ -f .env ]; then
        set -a
        # shellcheck disable=SC1091
        source .env 2>/dev/null || true
        set +a
    fi
    
    # MCP stdio servers need an open stdin - they exit on EOF. Use tail -f /dev/null
    # to keep a pipe open so the server stays alive waiting for backend connections.
    ( tail -f /dev/null 2>/dev/null | exec "$python_exec" "$server_script" ) >> "$log_file" 2>&1 &
    
    local pid=$!
    echo $pid > "/tmp/mcp-${server_name}.pid"
    
    # Wait a moment and check if process is still running
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}✅ ${server_name} started (PID: $pid)${NC}"
        echo -e "   Logs: $log_file"
        cd "$SCRIPT_DIR"
        return 0
    else
        echo -e "${RED}❌ ${server_name} failed to start${NC}"
        echo -e "   Check logs: tail -20 $log_file"
        cd "$SCRIPT_DIR"
        return 1
    fi
}

# Function to start a Node.js server with ts-node
start_node_server() {
    local server_name=$1
    local server_dir=$2
    local server_script=$3  # relative to server_dir, e.g. src/server.ts

    echo -e "${YELLOW}Starting ${server_name}...${NC}"

    if [ ! -d "$SCRIPT_DIR/$server_dir" ]; then
        echo -e "${RED}❌ $server_dir not found${NC}"
        return 1
    fi

    cd "$SCRIPT_DIR/$server_dir"

    if ! check_env_file "$server_dir"; then
        echo -e "${RED}❌ $server_dir/.env is missing or incomplete${NC}"
        return 1
    fi

    # Install node_modules if missing
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing npm dependencies...${NC}"
        npm install --silent
    fi

    if [ ! -f "$server_script" ]; then
        echo -e "${RED}❌ $server_script not found${NC}"
        return 1
    fi

    # Kill existing process if running
    if [ -f "/tmp/mcp-${server_name}.pid" ]; then
        local old_pid=$(cat "/tmp/mcp-${server_name}.pid" 2>/dev/null || echo "")
        if [ ! -z "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
            echo -e "${YELLOW}Stopping existing ${server_name} (PID: $old_pid)...${NC}"
            kill "$old_pid" 2>/dev/null || true
            sleep 1
        fi
    fi

    local log_file="/tmp/mcp-${server_name}.log"
    echo -e "${BLUE}Starting ${server_name}...${NC}"

    # Load .env
    if [ -f .env ]; then
        set -a
        # shellcheck disable=SC1091
        source .env 2>/dev/null || true
        set +a
    fi

    # Start with ts-node (keeps stdin open so the HTTP server stays alive)
    npx ts-node "$server_script" >> "$log_file" 2>&1 &

    local pid=$!
    echo $pid > "/tmp/mcp-${server_name}.pid"

    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}✅ ${server_name} started (PID: $pid)${NC}"
        echo -e "   Logs: $log_file"
        cd "$SCRIPT_DIR"
        return 0
    else
        echo -e "${RED}❌ ${server_name} failed to start${NC}"
        echo -e "   Check logs: tail -20 $log_file"
        cd "$SCRIPT_DIR"
        return 1
    fi
}

# Start all servers
FAILED=0

if [ -d "server-a-job-analysis" ]; then
    start_server "server-a" "server-a-job-analysis" "src/server.py" || FAILED=1
else
    echo -e "${RED}❌ server-a-job-analysis not found${NC}"
    FAILED=1
fi

if [ -d "server-b-template-builder" ]; then
    start_server "server-b" "server-b-template-builder" "src/server.py" || FAILED=1
else
    echo -e "${RED}❌ server-b-template-builder not found${NC}"
    FAILED=1
fi

if [ -d "server-c-monitoring" ]; then
    start_server "server-c-monitoring" "server-c-monitoring" "src/server.py" || FAILED=1
else
    echo -e "${RED}❌ server-c-monitoring not found${NC}"
    FAILED=1
fi

if [ -d "server-c-orchestrator" ]; then
    start_node_server "server-c-orchestrator" "server-c-orchestrator" "src/server.ts" || FAILED=1
else
    echo -e "${RED}❌ server-c-orchestrator not found${NC}"
    FAILED=1
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All MCP servers started successfully!${NC}"
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
else
    echo -e "${RED}❌ Some servers failed to start. Check logs above.${NC}"
    exit 1
fi

