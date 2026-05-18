"""
MCP Router for Agentic CRM
"""
from fastapi import APIRouter

from app.mcp.server import execute_mcp_tool, list_mcp_tools, mcp_health

mcp_router = APIRouter(prefix="/mcp", tags=["mcp"])

mcp_router.add_api_route("/execute", execute_mcp_tool, methods=["POST"])
mcp_router.add_api_route("/tools", list_mcp_tools, methods=["GET"])
mcp_router.add_api_route("/health", mcp_health, methods=["GET"])

__all__ = ["mcp_router"]
