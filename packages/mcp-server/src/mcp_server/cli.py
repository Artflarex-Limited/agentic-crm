"""
Agentic CRM MCP Server CLI

Usage:
    mcp-server                    # Run the MCP server
    mcp-server --help             # Show help
"""
from mcp_server.tools import mcp

if __name__ == "__main__":
    mcp.run()