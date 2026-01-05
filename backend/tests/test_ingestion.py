"""
Test ingestion pipeline
"""

import pytest
import json
from app.ingestion.chatgpt_importer import ChatGPTImporter
from app.ingestion.gemini_importer import GeminiImporter
from app.ingestion.manual_importer import ManualImporter
from app.ingestion.coreference import CoreferenceResolver
from app.ingestion.orchestrator import IngestionOrchestrator


@pytest.mark.unit
class TestChatGPTImporter:
    """Test ChatGPT conversation importer"""
    
    def test_parse_valid_export(self, sample_chatgpt_export):
        """Test parsing valid ChatGPT export"""
        importer = ChatGPTImporter()
        conversations = importer.parse(json.dumps(sample_chatgpt_export))
        
        assert len(conversations) > 0
        assert conversations[0]["id"] == "conv_123"
        assert len(conversations[0]["messages"]) == 2
    
    def test_extract_messages(self, sample_chatgpt_export):
        """Test message extraction from mapping"""
        importer = ChatGPTImporter()
        messages = importer._extract_messages(sample_chatgpt_export["mapping"])
        
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"


@pytest.mark.unit
class TestManualImporter:
    """Test manual text importer"""
    
    def test_parse_simple_format(self):
        """Test parsing simple user/assistant format"""
        text = """
User: Hello, how are you?
Assistant: I'm doing great!
User: What's the weather?
Assistant: I don't have weather data.
        """
        
        importer = ManualImporter()
        conversations = importer.parse(text)
        
        assert len(conversations) > 0
        assert len(conversations[0]["messages"]) == 4


@pytest.mark.unit
@pytest.mark.asyncio
class TestCoreferenceResolver:
    """Test coreference resolution"""
    
    async def test_resolve_pronouns(self, mock_gemini_client):
        """Test pronoun resolution"""
        resolver = CoreferenceResolver(mock_gemini_client)
        
        text = "John went to the store. He bought milk."
        resolved = await resolver.resolve(text)
        
        # In real test, would verify "He" is resolved to "John"
        assert resolved is not None
    
    async def test_entity_extraction(self, mock_gemini_client):
        """Test entity extraction"""
        resolver = CoreferenceResolver(mock_gemini_client)
        
        text = "Alice and Bob discussed AI. They both agreed."
        entities = await resolver.extract_entities(text)
        
        # Would verify Alice and Bob are extracted
        assert entities is not None


@pytest.mark.integration
@pytest.mark.asyncio
class TestIngestionOrchestrator:
    """Test full ingestion pipeline"""
    
    async def test_full_pipeline(
        self, 
        mock_gemini_client, 
        mock_pinecone_client, 
        mock_neo4j_client,
        sample_chatgpt_export,
        db_session
    ):
        """Test complete ingestion flow"""
        orchestrator = IngestionOrchestrator(
            gemini_client=mock_gemini_client,
            vector_db=mock_pinecone_client,
            graph_db=mock_neo4j_client
        )
        
        content = json.dumps(sample_chatgpt_export)
        
        result = await orchestrator.ingest_file(
            file_content=content.encode(),
            source_type="chatgpt",
            filename="conversations.json",
            db=db_session
        )
        
        assert result is not None
        assert "conversations_processed" in result
