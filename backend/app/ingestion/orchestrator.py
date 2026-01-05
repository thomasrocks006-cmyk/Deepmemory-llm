"""
Main ingestion orchestrator.
Coordinates parsing, coreference resolution, and database storage.
"""

from typing import Dict, Any, List
from app.ingestion.chatgpt_importer import ChatGPTImporter
from app.ingestion.gemini_importer import GeminiImporter
from app.ingestion.manual_importer import ManualImporter
from app.ingestion.coreference import CoreferenceResolver
from app.database import get_db
from app.models import Conversation, Message
from app.gemini_client import gemini_client
from app.llama_embeddings import get_llama_client
from app.vector_db import pinecone_client
from app.graph_db import neo4j_client
import logging
import uuid

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """
    Orchestrates the complete ingestion pipeline:
    1. Parse conversations from various sources
    2. Resolve coreferences
    3. Generate embeddings
    4. Store in databases (PostgreSQL, Pinecone, Neo4j)
    5. Extract entities for knowledge graph
    """
    
    def __init__(self):
        self.importers = {
            'chatgpt': ChatGPTImporter(),
            'gemini': GeminiImporter(),
            'grok': ManualImporter(),  # Grok uses manual format for now
            'manual': ManualImporter()
        }
        self.coreference_resolver = CoreferenceResolver()
    
    async def ingest_file(
        self,
        file_content: bytes,
        source_type: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Ingest a conversation file.
        
        Args:
            file_content: Raw file bytes
            source_type: 'chatgpt', 'gemini', 'grok', or 'manual'
            filename: Original filename
            
        Returns:
            Ingestion report with statistics
        """
        logger.info(f"Starting ingestion: {filename} ({source_type})")
        
        report = {
            'filename': filename,
            'source_type': source_type,
            'conversations_imported': 0,
            'messages_imported': 0,
            'entities_extracted': 0,
            'errors': []
        }
        
        try:
            # Step 1: Parse conversations
            importer = self.importers.get(source_type)
            if not importer:
                raise ValueError(f"Unknown source type: {source_type}")
            
            conversations = list(importer.parse(file_content))
            logger.info(f"Parsed {len(conversations)} conversations")
            
            # Step 2: Process each conversation
            for conv in conversations:
                try:
                    await self._process_conversation(conv, report)
                except Exception as e:
                    logger.error(f"Failed to process conversation: {e}")
                    report['errors'].append(str(e))
            
            logger.info(f"Ingestion complete: {report}")
            return report
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            report['errors'].append(str(e))
            return report
    
    async def _process_conversation(
        self,
        conv_data: Dict[str, Any],
        report: Dict[str, Any]
    ):
        """Process a single conversation through the full pipeline."""
        
        messages = conv_data['messages']
        metadata = conv_data['metadata']
        
        # Step 1: Coreference resolution
        logger.info("Resolving coreferences...")
        resolved_messages = await self.coreference_resolver.resolve_conversation(messages)
        
        # Step 2: Store in PostgreSQL
        logger.info("Storing in PostgreSQL...")
        conversation_id = await self._store_in_postgres(
            messages=resolved_messages,
            metadata=metadata
        )
        
        # Step 3: Generate embeddings and store in Pinecone
        logger.info("Generating embeddings...")
        await self._store_in_pinecone(
            messages=resolved_messages,
            conversation_id=conversation_id
        )
        
        # Step 4: Extract entities and build knowledge graph
        logger.info("Building knowledge graph...")
        entities_count = await self._build_knowledge_graph(
            messages=resolved_messages,
            conversation_id=conversation_id
        )
        
        # Update report
        report['conversations_imported'] += 1
        report['messages_imported'] += len(messages)
        report['entities_extracted'] += entities_count
    
    async def _store_in_postgres(
        self,
        messages: List[Dict],
        metadata: Dict
    ) -> str:
        """Store conversation and messages in PostgreSQL."""
        
        with get_db() as db:
            # Create conversation record
            conversation = Conversation(
                source=metadata['source'],
                title=metadata.get('title'),
                total_messages=metadata['total_messages'],
                metadata=metadata
            )
            db.add(conversation)
            db.flush()  # Get the ID
            
            # Create message records
            for msg in messages:
                message = Message(
                    conversation_id=conversation.id,
                    role=msg['role'],
                    content=msg['content'],
                    resolved_content=msg.get('resolved_content'),
                    timestamp=msg['timestamp'],
                    metadata=msg.get('metadata', {})
                )
                db.add(message)
            
            db.commit()
            
            return str(conversation.id)
    
    async def _store_in_pinecone(
        self,
        messages: List[Dict],
        conversation_id: str
    ):
        """Generate embeddings and store in Pinecone."""
        
        vectors = []
        
        # Get Llama embedding client
        llama_client = get_llama_client()
        
        for i, msg in enumerate(messages):
            # Use resolved content if available
            text = msg.get('resolved_content') or msg['content']
            
            # Generate multi-dimensional embeddings using Llama
            semantic_emb = llama_client.embed_text(text, task_type="retrieval_document")
            sentiment_emb = await llama_client.create_specialized_embedding(text, "sentiment")
            strategic_emb = await llama_client.create_specialized_embedding(text, "strategic")
            
            message_id = f"{conversation_id}-{i}"
            
            # Store in different namespaces
            for namespace, embedding in [
                ('semantic', semantic_emb),
                ('sentiment', sentiment_emb),
                ('strategic', strategic_emb)
            ]:
                pinecone_client.upsert_embedding(
                    vector_id=message_id,
                    embedding=embedding,
                    metadata={
                        'conversation_id': conversation_id,
                        'role': msg['role'],
                        'content': text[:1000],  # Truncate for metadata
                        'timestamp': msg['timestamp'].isoformat(),
                        'source': msg.get('source')
                    },
                    namespace=namespace
                )
    
    async def _build_knowledge_graph(
        self,
        messages: List[Dict],
        conversation_id: str
    ) -> int:
        """Extract entities and relationships, build knowledge graph."""
        
        # Combine messages for entity extraction
        full_text = '\n'.join(
            msg.get('resolved_content') or msg['content']
            for msg in messages
        )
        
        # Extract entities using Gemini
        extraction_prompt = f"""
        Extract entities and relationships from this conversation.
        
        Conversation:
        {full_text[:10000]}  # Limit to 10k chars
        
        Return JSON with:
        {{
            "entities": [
                {{"name": "EntityName", "type": "Person|Project|Concept|Location", "properties": {{...}}}}
            ],
            "relationships": [
                {{"from": "Entity1", "to": "Entity2", "type": "KNOWS|WORKS_ON|RELATES_TO", "properties": {{...}}}}
            ]
        }}
        """
        
        response = await gemini_client.generate_flash(
            prompt=extraction_prompt,
            response_format="json"
        )
        
        try:
            import json
            data = json.loads(response)
            
            # Create nodes
            for entity in data.get('entities', []):
                neo4j_client.create_or_update_node(
                    label=entity['type'],
                    name=entity['name'],
                    properties=entity.get('properties', {})
                )
            
            # Create relationships
            for rel in data.get('relationships', []):
                # Determine entity types (default to Person)
                from_type = next(
                    (e['type'] for e in data['entities'] if e['name'] == rel['from']),
                    'Person'
                )
                to_type = next(
                    (e['type'] for e in data['entities'] if e['name'] == rel['to']),
                    'Person'
                )
                
                neo4j_client.create_relationship(
                    from_label=from_type,
                    from_name=rel['from'],
                    to_label=to_type,
                    to_name=rel['to'],
                    relationship_type=rel['type'],
                    properties=rel.get('properties', {})
                )
            
            return len(data.get('entities', []))
            
        except Exception as e:
            logger.error(f"Knowledge graph extraction failed: {e}")
            return 0


# Global instance
ingestion_orchestrator = IngestionOrchestrator()
