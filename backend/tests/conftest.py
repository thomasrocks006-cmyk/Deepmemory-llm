"""
Pytest configuration and shared fixtures
"""

import pytest
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from faker import Faker

from app.models import Base
from app.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test settings with mock values"""
    return Settings(
        # Database
        database_url="sqlite:///./test.db",
        
        # Required settings
        secret_key="test-secret-key-12345",
        
        # API Keys (mock)
        google_api_key="test_api_key",
        google_cloud_project="test-project",
        pinecone_api_key="test_pinecone_key",
        pinecone_environment="test-env",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="test_password",
        
        # Other settings
        cors_origins="http://localhost:3000",
        debug=True
    )


@pytest.fixture(scope="function")
def db_session(test_settings) -> Generator[Session, None, None]:
    """Create a test database session"""
    engine = create_engine(
        test_settings.database_url,
        connect_args={"check_same_thread": False}  # SQLite only
    )
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def faker_instance():
    """Faker instance for generating test data"""
    return Faker()


@pytest.fixture
def sample_conversation_data(faker_instance):
    """Sample conversation data for testing"""
    return {
        "id": "test_conv_1",
        "title": faker_instance.sentence(),
        "user_id": "test_user",
        "messages": [
            {
                "role": "user",
                "content": "What is the meaning of life?",
            },
            {
                "role": "assistant",
                "content": "That's a profound question...",
            }
        ]
    }


@pytest.fixture
def sample_chatgpt_export():
    """Sample ChatGPT export format"""
    return {
        "id": "conv_123",
        "title": "Philosophy Discussion",
        "create_time": 1234567890.0,
        "mapping": {
            "msg_1": {
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Hello, how are you?"]}
                }
            },
            "msg_2": {
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["I'm doing well, thank you!"]}
                }
            }
        }
    }


@pytest.fixture
def sample_persona_data():
    """Sample persona/profile data"""
    return {
        "name": "John Doe",
        "core_values": ["honesty", "growth", "creativity"],
        "goals": ["Learn AI", "Build products", "Help others"],
        "fears": ["failure", "irrelevance"],
        "traits": {
            "openness": 85,
            "conscientiousness": 70,
            "extraversion": 60,
            "agreeableness": 75,
            "neuroticism": 40
        },
        "motivations": ["achievement", "autonomy", "mastery"],
        "conflicts": ["Work-life balance vs career growth"]
    }


# Mock classes for external services
class MockGeminiClient:
    """Mock Gemini API client"""
    
    async def generate_flash(self, prompt: str, **kwargs):
        """Mock generate_flash - matches actual GeminiClient"""
        return '{"facts": [], "entities": [], "sentiment": {}, "values": []}'
    
    async def generate_with_thinking(self, prompt: str, **kwargs):
        """Mock generate_with_thinking - matches actual GeminiClient"""
        return {
            "content": '{"patterns": [], "growth": "", "opportunities": [], "blind_spots": []}',
            "thinking": "Mock thinking process"
        }
    
    async def generate_stream(self, prompt: str, **kwargs):
        async def stream():
            for word in "This is a streamed response".split():
                yield word + " "
        return stream()
    
    def embed_text(self, text: str, **kwargs):
        """Mock embed_text - synchronous in actual client"""
        return [0.1] * 1024
    
    async def create_specialized_embedding(self, text: str, dimension: str):
        return [0.2] * 1024


class MockPineconeClient:
    """Mock Pinecone vector database"""
    
    def __init__(self):
        self.vectors = []
    
    def upsert_embedding(self, vector_id, embedding, metadata=None, namespace=None):
        """Match actual PineconeClient.upsert_embedding"""
        self.vectors.append({"id": vector_id, "values": embedding, "metadata": metadata})
        return True
    
    def query(self, query_embedding, top_k=10, filter=None, namespace=None):
        """Match actual PineconeClient.query"""
        return [
            {
                "id": f"vec_{i}",
                "score": 0.9 - (i * 0.1),
                "metadata": {
                    "content": f"Sample content {i}",
                    "type": "semantic"
                }
            }
            for i in range(min(top_k, 5))
        ]
    
    def multi_dimensional_query(self, query, dimensions=None):
        """Match actual PineconeClient method"""
        return self.query(query_embedding=[0.1]*1024, top_k=10)
    
    def get_index_stats(self):
        return {"total_vector_count": len(self.vectors)}


class MockNeo4jClient:
    """Mock Neo4j graph database"""
    
    def __init__(self):
        self.nodes = []
        self.relationships = []
        self.driver = MockNeo4jDriver()
    
    def create_constraints(self):
        pass
    
    def create_or_update_node(self, label, name, properties=None):
        """Match actual Neo4jClient.create_or_update_node"""
        self.nodes.append({"label": label, "name": name, "properties": properties})
        return {"name": name}
    
    def create_relationship(self, from_label, from_name, to_label, to_name, 
                           relationship_type, properties=None):
        """Match actual Neo4jClient.create_relationship"""
        self.relationships.append({
            "from_label": from_label,
            "from_name": from_name,
            "to_label": to_label,
            "to_name": to_name,
            "type": relationship_type,
            "properties": properties
        })
    
    def traverse_graph(self, start_name, relationship_types=None, max_depth=3):
        """Match actual Neo4jClient.traverse_graph"""
        return [
            {"name": "Related Entity 1", "type": "Person"},
            {"name": "Related Entity 2", "type": "Concept"}
        ]
    
    def close(self):
        pass


class MockNeo4jDriver:
    """Mock Neo4j driver for health checks"""
    def session(self):
        return MockNeo4jSession()


class MockNeo4jSession:
    """Mock Neo4j session"""
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def run(self, query, **kwargs):
        return None


@pytest.fixture
def mock_gemini_client():
    """Provide mock Gemini client"""
    return MockGeminiClient()


@pytest.fixture
def mock_pinecone_client():
    """Provide mock Pinecone client"""
    return MockPineconeClient()


@pytest.fixture
def mock_neo4j_client():
    """Provide mock Neo4j client"""
    return MockNeo4jClient()
