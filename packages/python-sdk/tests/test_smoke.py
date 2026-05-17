"""
Smoke tests for Agentic CRM Python SDK.
"""
from agentic_crm_sdk import AgenticCRM, AsyncAgenticCRM, SDKConfig


def test_sdk_config_defaults():
    config = SDKConfig()
    assert config.base_url == "http://localhost:8000"
    assert config.timeout == 30.0
    assert config.max_retries == 3


def test_sync_client_init():
    client = AgenticCRM({"base_url": "http://test.local"})
    assert client.base_url == "http://test.local"
    assert hasattr(client, "leads")
    assert hasattr(client, "contacts")
    assert hasattr(client, "deals")
    assert hasattr(client, "activities")
    assert hasattr(client, "agents")
    assert hasattr(client, "sequences")


def test_sync_client_default():
    client = AgenticCRM()
    assert client.base_url == "http://localhost:8000"


def test_async_client_init():
    client = AsyncAgenticCRM({"base_url": "http://test.local"})
    assert client.base_url == "http://test.local"