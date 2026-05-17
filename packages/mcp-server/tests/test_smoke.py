"""
Smoke tests for Agentic CRM MCP Server
"""
import pytest


def test_import():
    """Test that the MCP server package can be imported."""
    from mcp_server import __version__
    assert __version__ == "0.1.0"


def test_settings_defaults():
    """Test default settings."""
    from mcp_server import Settings
    settings = Settings()
    assert settings.agentic_crm_api_url == "http://localhost:8000"
    assert settings.agentic_crm_api_key == ""
    assert settings.timeout == 30.0


def test_tools_module_import():
    """Test that tools module can be imported."""
    from mcp_server import tools
    assert hasattr(tools, "mcp")


@pytest.mark.asyncio
async def test_tools_available():
    """Test that MCP tools are registered."""
    from mcp_server.tools import mcp
    assert mcp is not None
    assert hasattr(mcp, "add_tool")