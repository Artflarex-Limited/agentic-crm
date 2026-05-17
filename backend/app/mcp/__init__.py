"""
MCP (Model Context Protocol) Server for Agentic CRM

Provides Model Context Protocol interface for AI agents to interact with the CRM.
Exposes tools for lead management, contact operations, deal tracking, and agent actions.
"""
from app.mcp.router import mcp_router

__all__ = ["mcp_router"]