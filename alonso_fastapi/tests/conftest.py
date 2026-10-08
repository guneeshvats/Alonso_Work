# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app  # Import the FastAPI app

@pytest.fixture(scope="module")
def test_client():
    """Fixture to provide a test client for FastAPI routes."""
    with TestClient(app) as client:
        yield client
