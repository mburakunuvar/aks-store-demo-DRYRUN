"""
Tests for the description generation endpoint and helper functions.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app
from routers.description_generator import (
    _create_completion,
    _handle_local_llm,
    _handle_openai,
    _handle_azure_openai,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)


@pytest.fixture
def client():
    return TestClient(app)


def _mock_completion(content="Generated description."):
    """Return a mock chat completion response."""
    mock = MagicMock()
    mock.choices[0].message.content = content
    return mock


# --- _create_completion ---

def test_create_completion_calls_client_with_correct_args():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_completion("test")

    result = _create_completion(mock_client, "gpt-4", "Hello")

    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Hello"},
        ],
        temperature=0,
    )
    assert result == mock_client.chat.completions.create.return_value


def test_create_completion_uses_custom_system_prompt():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_completion()

    _create_completion(mock_client, "gpt-4", "prompt", system_prompt="Custom prompt")

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    assert messages[0]["content"] == "Custom prompt"


# --- _handle_local_llm ---

def test_handle_local_llm_raises_when_endpoint_missing(monkeypatch):
    monkeypatch.delenv("LOCAL_LLM_ENDPOINT", raising=False)
    with pytest.raises(ValueError, match="LOCAL_LLM_ENDPOINT"):
        _handle_local_llm("prompt")


def test_handle_local_llm_returns_description(monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_ENDPOINT", "http://localhost:8000/v1")

    mock_completion = _mock_completion("Local description")
    with patch("routers.description_generator.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.models.list.return_value = MagicMock(data=[MagicMock(id="local-model")])
        mock_client.chat.completions.create.return_value = mock_completion

        result = _handle_local_llm("describe this")

    assert result == "Local description"


# --- _handle_openai ---

def test_handle_openai_raises_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_ORG_ID", "org-123")
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        _handle_openai("prompt")


def test_handle_openai_raises_when_org_id_missing(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_ORG_ID", raising=False)
    with pytest.raises(ValueError, match="OPENAI_ORG_ID"):
        _handle_openai("prompt")


def test_handle_openai_returns_description(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_ORG_ID", "org-123")

    mock_completion = _mock_completion("OpenAI description")
    with patch("routers.description_generator.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_completion

        result = _handle_openai("describe this")

    assert result == "OpenAI description"


# --- _handle_azure_openai ---

def test_handle_azure_openai_raises_when_deployment_missing(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT_NAME", raising=False)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
    with pytest.raises(ValueError, match="AZURE_OPENAI_DEPLOYMENT_NAME"):
        _handle_azure_openai("prompt", use_azure_ad=False)


def test_handle_azure_openai_raises_when_endpoint_missing(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT"):
        _handle_azure_openai("prompt", use_azure_ad=False)


def test_handle_azure_openai_raises_when_api_key_missing(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        _handle_azure_openai("prompt", use_azure_ad=False)


def test_handle_azure_openai_api_key_returns_description(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_completion = _mock_completion("Azure description")
    with patch("routers.description_generator.AzureOpenAI") as mock_azure_cls:
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_completion

        result = _handle_azure_openai("describe this", use_azure_ad=False)

    assert result == "Azure description"


def test_handle_azure_openai_azure_ad_returns_description(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")

    mock_completion = _mock_completion("Azure AD description")
    # DefaultAzureCredential and get_bearer_token_provider are patched to
    # prevent real Azure identity lookups during unit tests.
    with patch("routers.description_generator.AzureOpenAI") as mock_azure_cls, \
         patch("routers.description_generator.DefaultAzureCredential"), \
         patch("routers.description_generator.get_bearer_token_provider"):
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_completion

        result = _handle_azure_openai("describe this", use_azure_ad=True)

    assert result == "Azure AD description"


# --- /generate/description endpoint ---

def test_generate_description_endpoint_openai(client, monkeypatch):
    monkeypatch.setenv("USE_LOCAL_LLM", "false")
    monkeypatch.setenv("USE_AZURE_OPENAI", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_ORG_ID", "org-123")

    mock_completion = _mock_completion("A wonderful toy for cats!")
    with patch("routers.description_generator.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_completion

        response = client.post(
            "/generate/description",
            json={"name": "Cat Toy", "tags": ["fun", "cats", "interactive"]},
        )

    assert response.status_code == 200
    assert response.json()["description"] == "A wonderful toy for cats!"


def test_generate_description_endpoint_azure(client, monkeypatch):
    monkeypatch.setenv("USE_LOCAL_LLM", "false")
    monkeypatch.setenv("USE_AZURE_OPENAI", "true")
    monkeypatch.setenv("USE_AZURE_AD", "false")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_completion = _mock_completion("Azure-generated toy description")
    with patch("routers.description_generator.AzureOpenAI") as mock_azure_cls:
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_completion

        response = client.post(
            "/generate/description",
            json={"name": "Dog Ball", "tags": ["durable", "bouncy"]},
        )

    assert response.status_code == 200
    assert response.json()["description"] == "Azure-generated toy description"


def test_generate_description_endpoint_local_llm(client, monkeypatch):
    monkeypatch.setenv("USE_LOCAL_LLM", "true")
    monkeypatch.setenv("LOCAL_LLM_ENDPOINT", "http://localhost:8000/v1")

    mock_completion = _mock_completion("Local LLM description")
    with patch("routers.description_generator.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.models.list.return_value = MagicMock(data=[MagicMock(id="local-model")])
        mock_client.chat.completions.create.return_value = mock_completion

        response = client.post(
            "/generate/description",
            json={"name": "Bird Feeder", "tags": ["outdoor", "birds"]},
        )

    assert response.status_code == 200
    assert response.json()["description"] == "Local LLM description"


def test_generate_description_endpoint_missing_tags_returns_422(client):
    """Pydantic validation rejects requests missing the required 'tags' field."""
    response = client.post("/generate/description", json={"name": "Cat Toy"})
    assert response.status_code == 422


def test_generate_description_endpoint_missing_name_returns_422(client):
    """Pydantic validation rejects requests missing the required 'name' field."""
    response = client.post("/generate/description", json={"tags": ["fun"]})
    assert response.status_code == 422


def test_generate_description_endpoint_propagates_error_as_500(client, monkeypatch):
    """Backend errors are surfaced as HTTP 500."""
    monkeypatch.setenv("USE_LOCAL_LLM", "false")
    monkeypatch.setenv("USE_AZURE_OPENAI", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_ORG_ID", raising=False)

    response = client.post(
        "/generate/description",
        json={"name": "Cat Toy", "tags": ["fun"]},
    )
    assert response.status_code == 500


def test_user_prompt_template_contains_name_and_tags():
    """USER_PROMPT_TEMPLATE should include the name and tags placeholders."""
    prompt = USER_PROMPT_TEMPLATE.format(name="Widget", tags="tag1, tag2")
    assert "Widget" in prompt
    assert "tag1, tag2" in prompt
