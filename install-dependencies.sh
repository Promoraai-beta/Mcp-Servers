#!/bin/bash

# Install MCP dependencies for all servers

echo "📦 Installing MCP dependencies..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
    exit 1
fi

# Install for each server
for server_dir in server-*; do
    if [ -d "$server_dir" ]; then
        echo -e "${GREEN}Installing dependencies for ${server_dir}...${NC}"
        cd "$server_dir"
        
        if [ -f "requirements.txt" ]; then
            pip3 install -q -r requirements.txt 2>&1 | grep -v "already satisfied" || true
            echo -e "${GREEN}  ✅ ${server_dir} dependencies installed${NC}"
        else
            echo -e "${YELLOW}  ⚠️  No requirements.txt found in ${server_dir}${NC}"
        fi
        
        cd ..
    fi
done

echo ""
echo -e "${GREEN}✅ All MCP dependencies installed!${NC}"
echo ""
echo "To verify installation, run:"
echo "  python3 -c \"from mcp.server import Server; print('✅ MCP SDK installed!')\""

