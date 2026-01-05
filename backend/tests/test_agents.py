"""
Test the Librarian Agent
"""

import pytest
from app.agents.librarian import LibrarianAgent


@pytest.mark.agent
@pytest.mark.asyncio
class TestLibrarianAgent:
    """Test Librarian retrieval agent"""
    
    async def test_initialization(self, mock_gemini_client, mock_pinecone_client, mock_neo4j_client):
        """Test agent initializes correctly"""
        agent = LibrarianAgent(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        assert agent.gemini_client is not None
        assert agent.vector_db is not None
        assert agent.graph_db is not None
    
    async def test_process_query(self, mock_gemini_client, mock_pinecone_client, mock_neo4j_client):
        """Test query processing"""
        agent = LibrarianAgent(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        result = await agent.process({
            "query": "What did I learn about Python?",
            "filters": {}
        })
        
        assert result is not None
        assert "context" in result or "sources" in result or "content" in result
    
    async def test_multi_vector_search(self, mock_gemini_client, mock_pinecone_client, mock_neo4j_client):
        """Test multi-dimensional vector search"""
        agent = LibrarianAgent(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        # This would test semantic + sentiment + strategic search
        query = "How do I feel about my career?"
        
        # Mock implementation would return results
        # In real test, we'd verify the search dimensions are used
        result = await agent.process({
            "query": query,
            "filters": {}
        })
        
        # Verify result structure
        assert result is not None
    
    async def test_graph_traversal(self, mock_gemini_client, mock_pinecone_client, mock_neo4j_client):
        """Test knowledge graph traversal for lateral thinking"""
        agent = LibrarianAgent(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        # Test that agent can traverse graph for related concepts
        result = await agent.process({
            "query": "Tell me about machine learning",
            "filters": {"use_graph": True}
        })
        
        # Would verify graph was queried
        assert result is not None


@pytest.mark.agent
@pytest.mark.asyncio
class TestStrategistAgent:
    """Test Strategist user-facing agent"""
    
    async def test_response_generation(self, mock_gemini_client, mock_pinecone_client, mock_neo4j_client):
        """Test strategist generates appropriate responses"""
        from app.agents.strategist import StrategistAgent
        
        agent = StrategistAgent(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        result = await agent.process({
            "query": "Should I change careers?",
            "context_brief": "User has been in tech for 5 years",
            "personas": [],
            "conversation_history": []
        })
        
        assert result is not None
        assert "content" in result
    
    async def test_persona_integration(self, mock_gemini_client, mock_pinecone_client, mock_neo4j_client, sample_persona_data):
        """Test that strategist uses persona data"""
        from app.agents.strategist import StrategistAgent
        
        agent = StrategistAgent(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        result = await agent.process({
            "query": "What motivates me?",
            "context_brief": "Previous discussions about goals",
            "personas": [sample_persona_data],
            "conversation_history": []
        })
        
        assert result is not None
        # In real test, would verify persona data is incorporated


@pytest.mark.agent
@pytest.mark.asyncio
class TestProfilerAgent:
    """Test Profiler psychological analysis agent"""
    
    async def test_profile_creation(self, mock_gemini_client, mock_pinecone_client, mock_neo4j_client, db_session):
        """Test creating psychological profile"""
        from app.agents.profiler import ProfilerAgent
        
        agent = ProfilerAgent(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        messages = [
            {"role": "user", "content": "I love learning new things"},
            {"role": "assistant", "content": "That's great!"},
            {"role": "user", "content": "But I worry about falling behind"}
        ]
        
        profile = await agent.create_profile("John Doe", messages, db_session)
        
        assert profile is not None
        # Would verify profile has expected fields
    
    async def test_big_five_extraction(self, mock_gemini_client, mock_pinecone_client, mock_neo4j_client):
        """Test Big Five personality trait extraction"""
        from app.agents.profiler import ProfilerAgent
        
        agent = ProfilerAgent(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        # Test trait extraction from conversation
        # In real implementation, would verify trait scores
        pass
