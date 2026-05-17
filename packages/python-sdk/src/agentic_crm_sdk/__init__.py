"""
Agentic CRM Python SDK

A Python SDK for interacting with the Agentic CRM API.
"""
from agentic_crm_sdk.client import AgenticCRM
from agentic_crm_sdk.async_client import AsyncAgenticCRM
from agentic_crm_sdk.config import SDKConfig

__version__ = "0.1.0"
__all__ = ["AgenticCRM", "AsyncAgenticCRM", "SDKConfig"]