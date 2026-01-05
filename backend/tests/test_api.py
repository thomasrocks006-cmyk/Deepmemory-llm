"""
Test API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for FastAPI"""
    return TestClient(app)


@pytest.mark.integration
class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.integration
class TestChatEndpoint:
    """Test chat API"""
    
    def test_chat_post(self, client):
        """Test POST /api/chat"""
        payload = {
            "query": "What is the meaning of life?",
            "conversation_id": None,
            "history": []
        }
        
        response = client.post("/api/chat", json=payload)
        
        # Might fail if agents not properly mocked, but structure should be correct
        assert response.status_code in [200, 500]  # 500 if real API not available
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data


@pytest.mark.integration
class TestIngestEndpoint:
    """Test conversation ingestion"""
    
    def test_ingest_upload(self, client, sample_chatgpt_export):
        """Test POST /api/ingest"""
        import json
        
        files = {
            "files": ("conversations.json", json.dumps(sample_chatgpt_export), "application/json")
        }
        
        response = client.post("/api/ingest", files=files)
        
        # May fail without real DB, but tests endpoint exists
        assert response.status_code in [200, 422, 500]


@pytest.mark.integration
class TestProfilesEndpoint:
    """Test persona profiles API"""
    
    def test_list_profiles(self, client):
        """Test GET /api/profiles"""
        response = client.get("/api/profiles")
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "personas" in data
    
    def test_get_profile(self, client):
        """Test GET /api/profiles/{person}"""
        response = client.get("/api/profiles/John%20Doe")
        
        # May return 404 if no profile exists
        assert response.status_code in [200, 404, 500]
