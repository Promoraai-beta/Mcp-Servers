#!/usr/bin/env python3
"""
Simple test script to verify MCP servers are running and can respond
"""
import json
import subprocess
import sys
import time
import os

def test_mcp_server(server_path, server_name):
    """Test an MCP server by sending initialization and listing tools"""
    print(f"\n{'='*60}")
    print(f"Testing {server_name}")
    print(f"{'='*60}")
    
    try:
        # Start the server process
        proc = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print(f"Sending initialize request...")
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()
        
        # Wait for response
        time.sleep(1)
        
        # Read response
        response_line = proc.stdout.readline()
        if response_line:
            try:
                response = json.loads(response_line.strip())
                print(f"✅ Initialize response received: {response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
            except json.JSONDecodeError:
                print(f"⚠️  Non-JSON response: {response_line[:100]}")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        proc.stdin.write(json.dumps(initialized_notification) + "\n")
        proc.stdin.flush()
        
        # List tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        print(f"Requesting tools list...")
        proc.stdin.write(json.dumps(tools_request) + "\n")
        proc.stdin.flush()
        
        time.sleep(1)
        
        response_line = proc.stdout.readline()
        if response_line:
            try:
                response = json.loads(response_line.strip())
                tools = response.get('result', {}).get('tools', [])
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')[:60]}...")
            except json.JSONDecodeError:
                print(f"⚠️  Non-JSON response: {response_line[:100]}")
        
        # Clean up
        proc.terminate()
        proc.wait(timeout=2)
        print(f"✅ {server_name} test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error testing {server_name}: {e}")
        if 'proc' in locals():
            proc.terminate()
        return False

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    servers = [
        ("server-a-job-analysis/src/server.py", "Server A (Job Analysis)"),
        ("server-b-template-builder/src/server.py", "Server B (Template Builder)"),
        ("server-c-monitoring/src/server.py", "Server C (Monitoring)")
    ]
    
    print("🧪 Testing MCP Servers")
    print("=" * 60)
    
    results = []
    for server_path, server_name in servers:
        full_path = os.path.join(script_dir, server_path)
        if os.path.exists(full_path):
            result = test_mcp_server(full_path, server_name)
            results.append((server_name, result))
        else:
            print(f"❌ Server not found: {full_path}")
            results.append((server_name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    for server_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {server_name}")





