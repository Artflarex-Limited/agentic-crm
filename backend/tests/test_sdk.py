"""
Tests for Agentic CRM Python SDK.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from agentic_crm_sdk import AgenticCRM, SDKConfig
from agentic_crm_sdk.client import AgenticCRM


class TestSDKConfig:
    def test_default_config(self):
        config = SDKConfig()
        assert config.base_url == "http://localhost:8000"
        assert config.api_key is None
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_custom_config(self):
        config = SDKConfig(
            base_url="https://api.example.com",
            api_key="test-key",
            timeout=60.0,
            max_retries=5,
        )
        assert config.base_url == "https://api.example.com"
        assert config.api_key == "test-key"
        assert config.timeout == 60.0
        assert config.max_retries == 5

    def test_config_from_dict(self):
        config = SDKConfig(**{"base_url": "https://api.example.com", "api_key": "key"})
        assert config.base_url == "https://api.example.com"
        assert config.api_key == "key"


class TestAgenticCRMClient:
    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_client_initialization(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM()

        assert client.base_url == "http://localhost:8000"
        assert isinstance(client.config, SDKConfig)
        mock_httpx_client.assert_called_once()

    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_client_with_config(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_httpx_client.return_value = mock_client_instance

        config = SDKConfig(base_url="https://api.example.com", api_key="secret")
        client = AgenticCRM(config)

        assert client.base_url == "https://api.example.com"
        assert client.config.api_key == "secret"

    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_client_with_dict_config(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM({"base_url": "https://api.example.com", "api_key": "secret"})

        assert client.base_url == "https://api.example.com"
        assert client.config.api_key == "secret"

    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_build_headers_without_key(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM()
        headers = client._build_headers()

        assert "Content-Type" in headers
        assert "User-Agent" in headers
        assert "Authorization" not in headers

    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_build_headers_with_key(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM({"api_key": "my-secret-key"})
        headers = client._build_headers()

        assert headers["Authorization"] == "Bearer my-secret-key"


class TestLeadsClient:
    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_list_leads(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"leads": []}
        mock_client_instance.request.return_value = mock_response
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM()
        client.leads.list()

        mock_client_instance.request.assert_called_once()

    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_get_lead(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "Test Lead"}
        mock_client_instance.request.return_value = mock_response
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM()
        client.leads.get(1)

        mock_client_instance.request.assert_called_once()

    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_create_lead(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "name": "New Lead"}
        mock_client_instance.request.return_value = mock_response
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM()
        result = client.leads.create({"name": "New Lead", "email": "test@example.com"})

        mock_client_instance.request.assert_called_once()


class TestContactsClient:
    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_list_contacts(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"contacts": []}
        mock_client_instance.request.return_value = mock_response
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM()
        client.contacts.list()

        mock_client_instance.request.assert_called_once()


class TestDealsClient:
    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_list_deals(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"deals": []}
        mock_client_instance.request.return_value = mock_response
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM()
        client.deals.list()

        mock_client_instance.request.assert_called_once()


class TestAgentsClient:
    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_pause_agent(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "status": "paused"}
        mock_client_instance.request.return_value = mock_response
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM()
        client.agents.pause(1)

        mock_client_instance.request.assert_called_once()

    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_resume_agent(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "status": "active"}
        mock_client_instance.request.return_value = mock_response
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM()
        client.agents.resume(1)

        mock_client_instance.request.assert_called_once()


class TestSequencesClient:
    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_list_sequences(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"sequences": []}
        mock_client_instance.request.return_value = mock_response
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM()
        client.sequences.list()

        mock_client_instance.request.assert_called_once()

    @patch("agentic_crm_sdk.client.httpx.Client")
    def test_enroll_lead(self, mock_httpx_client):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "enrolled"}
        mock_client_instance.request.return_value = mock_response
        mock_httpx_client.return_value = mock_client_instance

        client = AgenticCRM()
        client.sequences.enroll_lead(sequence_id=1, lead_id=2)

        mock_client_instance.request.assert_called_once()