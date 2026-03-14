"""
Tests for the health endpoint in main.py.
"""
import os
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_returns_ok(client):
    """Health endpoint returns 200 and status=ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_always_includes_description_capability(client):
    """Health endpoint always lists 'description' as a capability."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "description" in response.json()["capabilities"]


def test_health_no_dalle_excludes_image_capability(client, monkeypatch):
    """Health endpoint excludes 'image' when DALL-E env vars are absent."""
    monkeypatch.delenv("AZURE_OPENAI_DALLE_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DALLE_DEPLOYMENT_NAME", raising=False)

    response = client.get("/health")
    assert response.status_code == 200
    assert "image" not in response.json()["capabilities"]


def test_health_with_dalle_endpoint_and_deployment_includes_image(client, monkeypatch):
    """Health endpoint includes 'image' when DALL-E endpoint and deployment name are set."""
    monkeypatch.setenv("AZURE_OPENAI_DALLE_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DALLE_DEPLOYMENT_NAME", "dall-e-3")

    response = client.get("/health")
    assert response.status_code == 200
    assert "image" in response.json()["capabilities"]


def test_health_with_azure_endpoint_and_deployment_includes_image(client, monkeypatch):
    """Health endpoint includes 'image' when AZURE_OPENAI_ENDPOINT and deployment name are set."""
    monkeypatch.delenv("AZURE_OPENAI_DALLE_ENDPOINT", raising=False)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DALLE_DEPLOYMENT_NAME", "dall-e-3")

    response = client.get("/health")
    assert response.status_code == 200
    assert "image" in response.json()["capabilities"]


def test_health_returns_version(client):
    """Health endpoint includes a 'version' field in the response body."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "version" in response.json()
