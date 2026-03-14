"""
Tests for the image generation endpoint and helper functions.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app
from routers.image_generator import (
    _handle_azure_openai,
    USER_PROMPT_TEMPLATE,
)


@pytest.fixture
def client():
    return TestClient(app)


def _mock_image_response(url="https://example.com/image.png"):
    """Return a mock image generation response."""
    mock = MagicMock()
    mock.model_dump_json.return_value = json.dumps({"data": [{"url": url}]})
    return mock


# --- _handle_azure_openai (image) ---

def test_handle_azure_openai_raises_when_endpoint_missing(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_DALLE_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    with pytest.raises(ValueError, match="AZURE_OPENAI_DALLE_ENDPOINT"):
        _handle_azure_openai("a prompt", use_azure_ad=False)


def test_handle_azure_openai_raises_when_deployment_missing(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DALLE_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.delenv("AZURE_OPENAI_DALLE_DEPLOYMENT_NAME", raising=False)
    with pytest.raises(ValueError, match="AZURE_OPENAI_DALLE_DEPLOYMENT_NAME"):
        _handle_azure_openai("a prompt", use_azure_ad=False)


def test_handle_azure_openai_raises_when_api_version_missing(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DALLE_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DALLE_DEPLOYMENT_NAME", "dall-e-3")
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    with pytest.raises(ValueError, match="AZURE_OPENAI_API_VERSION"):
        _handle_azure_openai("a prompt", use_azure_ad=False)


def test_handle_azure_openai_raises_when_api_key_missing(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DALLE_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DALLE_DEPLOYMENT_NAME", "dall-e-3")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        _handle_azure_openai("a prompt", use_azure_ad=False)


def test_handle_azure_openai_api_key_returns_image_url(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DALLE_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DALLE_DEPLOYMENT_NAME", "dall-e-3")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_response = _mock_image_response("https://example.com/cat.png")
    with patch("routers.image_generator.AzureOpenAI") as mock_azure_cls:
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        mock_client.images.generate.return_value = mock_response

        url = _handle_azure_openai("a cute cat", use_azure_ad=False)

    assert url == "https://example.com/cat.png"


def test_handle_azure_openai_azure_ad_returns_image_url(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DALLE_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DALLE_DEPLOYMENT_NAME", "dall-e-3")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    mock_response = _mock_image_response("https://example.com/dog.png")
    # DefaultAzureCredential and get_bearer_token_provider are patched to
    # prevent real Azure identity lookups during unit tests.
    with patch("routers.image_generator.AzureOpenAI") as mock_azure_cls, \
         patch("routers.image_generator.DefaultAzureCredential"), \
         patch("routers.image_generator.get_bearer_token_provider"):
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        mock_client.images.generate.return_value = mock_response

        url = _handle_azure_openai("a cute dog", use_azure_ad=True)

    assert url == "https://example.com/dog.png"


def test_handle_azure_openai_falls_back_to_azure_endpoint(monkeypatch):
    """If AZURE_OPENAI_DALLE_ENDPOINT is absent, AZURE_OPENAI_ENDPOINT is used."""
    monkeypatch.delenv("AZURE_OPENAI_DALLE_ENDPOINT", raising=False)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://fallback.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DALLE_DEPLOYMENT_NAME", "dall-e-3")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_response = _mock_image_response()
    with patch("routers.image_generator.AzureOpenAI") as mock_azure_cls:
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        mock_client.images.generate.return_value = mock_response

        url = _handle_azure_openai("a pet image", use_azure_ad=False)

    assert url == "https://example.com/image.png"


# --- /generate/image endpoint ---

def test_generate_image_endpoint_returns_url(client, monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DALLE_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DALLE_DEPLOYMENT_NAME", "dall-e-3")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("USE_AZURE_AD", "false")

    mock_response = _mock_image_response("https://example.com/generated.png")
    with patch("routers.image_generator.AzureOpenAI") as mock_azure_cls:
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        mock_client.images.generate.return_value = mock_response

        response = client.post(
            "/generate/image",
            json={"name": "Cat Scratcher", "description": "A fun scratching post"},
        )

    assert response.status_code == 200
    assert response.json()["image"] == "https://example.com/generated.png"


def test_generate_image_endpoint_missing_name_returns_422(client):
    """Pydantic validation rejects requests missing the required 'name' field."""
    response = client.post("/generate/image", json={"description": "A fun toy"})
    assert response.status_code == 422


def test_generate_image_endpoint_missing_description_returns_422(client):
    """Pydantic validation rejects requests missing the required 'description' field."""
    response = client.post("/generate/image", json={"name": "Cat Toy"})
    assert response.status_code == 422


def test_generate_image_endpoint_missing_endpoint_returns_500(client, monkeypatch):
    """Missing Azure endpoint configuration surfaces as HTTP 500."""
    monkeypatch.delenv("AZURE_OPENAI_DALLE_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.setenv("USE_AZURE_AD", "false")

    response = client.post(
        "/generate/image",
        json={"name": "Cat Toy", "description": "A fun toy for cats"},
    )
    assert response.status_code == 500


def test_generate_image_calls_images_generate_with_n_equals_1(client, monkeypatch):
    """The image endpoint always requests exactly one image (n=1)."""
    monkeypatch.setenv("AZURE_OPENAI_DALLE_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DALLE_DEPLOYMENT_NAME", "dall-e-3")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("USE_AZURE_AD", "false")

    mock_response = _mock_image_response()
    with patch("routers.image_generator.AzureOpenAI") as mock_azure_cls:
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        mock_client.images.generate.return_value = mock_response

        client.post(
            "/generate/image",
            json={"name": "Widget", "description": "A cool widget"},
        )

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs.get("n") == 1


def test_user_prompt_template_contains_name_and_description():
    """USER_PROMPT_TEMPLATE should include the name and description placeholders."""
    prompt = USER_PROMPT_TEMPLATE.format(name="Cat Toy", description="A fun toy")
    assert "Cat Toy" in prompt
    assert "A fun toy" in prompt
