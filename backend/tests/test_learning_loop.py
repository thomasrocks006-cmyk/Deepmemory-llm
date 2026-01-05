"""
Test learning loop functionality
"""

import pytest
from datetime import datetime
from app.learning_loop import LearningLoop
from app.models import Conversation, Message, Scratchpad, Conflict, Insight


@pytest.mark.asyncio
class TestLearningLoop:
    """Test continuous learning system"""
    
    async def test_post_turn_extraction(
        self, 
        mock_gemini_client, 
        mock_pinecone_client, 
        mock_neo4j_client,
        db_session
    ):
        """Test fact extraction after assistant turn"""
        loop = LearningLoop(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        # Create test conversation
        conv = Conversation(
            id="test_conv",
            title="Test",
            user_id="test_user"
        )
        db_session.add(conv)
        
        msg = Message(
            id="msg_1",
            conversation_id="test_conv",
            role="assistant",
            content="You mentioned loving Python and machine learning."
        )
        db_session.add(msg)
        db_session.commit()
        
        result = await loop.post_turn_extraction(
            conversation_id="test_conv",
            message_id="msg_1",
            db=db_session
        )
        
        assert result is not None
        assert "extracted" in result
    
    async def test_conflict_detection(
        self,
        mock_gemini_client,
        mock_pinecone_client,
        mock_neo4j_client,
        db_session
    ):
        """Test detecting contradictions"""
        loop = LearningLoop(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        # Test with contradicting facts
        facts = [
            "I love working remotely",
            "I hate working from home"
        ]
        
        conflicts = await loop._detect_conflicts(facts, db_session)
        
        # Would verify conflicts are detected
        assert conflicts is not None
    
    async def test_scratchpad_update(
        self,
        mock_gemini_client,
        mock_pinecone_client,
        mock_neo4j_client,
        db_session
    ):
        """Test scratchpad living document updates"""
        loop = LearningLoop(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        conv = Conversation(
            id="test_conv",
            title="Test",
            user_id="test_user"
        )
        db_session.add(conv)
        db_session.commit()
        
        extracted = {
            "facts": ["User loves Python"],
            "values": ["Learning"],
            "sentiment": {"valence": 80}
        }
        
        await loop._update_scratchpad("test_conv", extracted, db_session)
        
        # Verify scratchpad was created/updated
        scratchpad = db_session.query(Scratchpad).filter_by(
            conversation_id="test_conv"
        ).first()
        
        assert scratchpad is not None
    
    async def test_reflection_event(
        self,
        mock_gemini_client,
        mock_pinecone_client,
        mock_neo4j_client,
        db_session
    ):
        """Test periodic reflection generation"""
        loop = LearningLoop(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        # Create conversation with messages
        conv = Conversation(
            id="test_conv",
            title="Test",
            user_id="test_user"
        )
        db_session.add(conv)
        
        for i in range(5):
            msg = Message(
                id=f"msg_{i}",
                conversation_id="test_conv",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}"
            )
            db_session.add(msg)
        
        db_session.commit()
        
        result = await loop.reflection_event("test_conv", db_session)
        
        assert result is not None
    
    async def test_subconscious_agent(
        self,
        mock_gemini_client,
        mock_pinecone_client,
        mock_neo4j_client,
        db_session
    ):
        """Test background insight generation"""
        loop = LearningLoop(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        # Create test data
        conv = Conversation(
            id="test_conv",
            title="Test",
            user_id="test_user",
            created_at=datetime.utcnow()
        )
        db_session.add(conv)
        
        for i in range(10):
            msg = Message(
                id=f"msg_{i}",
                conversation_id="test_conv",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Deep message {i}"
            )
            db_session.add(msg)
        
        db_session.commit()
        
        insights = await loop.subconscious_agent(db_session, lookback_days=7)
        
        assert insights is not None
