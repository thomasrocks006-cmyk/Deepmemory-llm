"""
Database models for DeepMemory LLM application.
Defines SQLAlchemy models for PostgreSQL.
"""

from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ARRAY, Boolean, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSTZRANGE
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

Base = declarative_base()


class Conversation(Base):
    """Stores conversation metadata."""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(20), nullable=False)  # 'chatgpt', 'gemini', 'grok'
    title = Column(Text)
    date_range = Column(TSTZRANGE)
    total_messages = Column(Integer)
    ingestion_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    conversation_metadata = Column(JSONB)  # Renamed from 'metadata' - reserved in SQLAlchemy
    importance_score = Column(Integer, default=5)


class Message(Base):
    """Stores individual messages with multi-dimensional embeddings."""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'))
    role = Column(String(10), nullable=False)  # 'user', 'assistant'
    content = Column(Text, nullable=False)
    resolved_content = Column(Text)  # After coreference resolution
    timestamp = Column(TIMESTAMP(timezone=True))
    
    # Multi-dimensional embeddings (1024-dim for Llama)
    semantic_embedding = Column(Vector(1024))
    sentiment_embedding = Column(Vector(1024))
    strategic_embedding = Column(Vector(1024))
    
    message_metadata = Column(JSONB)  # Renamed from 'metadata' - reserved in SQLAlchemy
    entities = Column(ARRAY(Text))  # Extracted people, places, projects


class Persona(Base):
    """Stores psychological profiles of people mentioned in conversations."""
    __tablename__ = "personas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_name = Column(String(255), unique=True, nullable=False)
    profile = Column(JSONB, nullable=False)
    version = Column(Integer, default=1)
    confidence_score = Column(Numeric(3, 2))
    first_mentioned = Column(TIMESTAMP(timezone=True))
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now())
    total_references = Column(Integer, default=0)
    previous_versions = Column(ARRAY(JSONB))


class Summary(Base):
    """Stores hierarchical summaries at different compression levels."""
    __tablename__ = "summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)  # For conversation-specific summaries
    level = Column(String(20), nullable=False)  # 'L1_Session', 'L2_Project', 'L3_Identity'
    tier = Column(Integer)  # 1, 2, or 3 (alternative to level)
    scope_id = Column(UUID(as_uuid=True))  # References conversation, project, or user
    content = Column(Text, nullable=False)  # Alias for summary_text
    summary_text = Column(Text)  # Legacy column
    token_count = Column(Integer)
    compression_ratio = Column(Numeric(5, 2))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())


class Conflict(Base):
    """Tracks detected conflicts in data for resolution."""
    __tablename__ = "conflicts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50))  # 'person', 'project', 'fact', 'document'
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    conflict_type = Column(String(100))  # 'self_contradiction', 'cross_contradiction', 'hallucination'
    statement_a = Column(Text)  # First statement (old_value kept for compatibility)
    statement_b = Column(Text)  # Conflicting statement (new_value kept for compatibility)
    old_value = Column(Text)  # Alias for statement_a
    new_value = Column(Text)  # Alias for statement_b
    explanation = Column(Text)  # Why they conflict
    severity = Column(String(20))  # 'minor', 'moderate', 'critical'
    location_data = Column(Text)  # JSON with document IDs and excerpts
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    resolved = Column(Boolean, default=False)
    resolution = Column(Text)
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)


class Scratchpad(Base):
    """Stores the living document of current state."""
    __tablename__ = "scratchpad"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=True)  # Optional, for user-specific scratchpads
    conversation_id = Column(String(255), nullable=True)  # For conversation-specific scratchpads
    content = Column(Text, nullable=False)
    token_count = Column(Integer)
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    version = Column(Integer, default=1)


class Insight(Base):
    """Stores proactive insights from the subconscious agent."""
    __tablename__ = "insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)  # For conversation-specific insights
    insight_type = Column(String(50))  # 'pattern', 'conflict', 'suggestion', 'reflection', 'subconscious'
    title = Column(String(255))
    content = Column(Text, nullable=False)
    confidence_score = Column(Numeric(3, 2))
    insight_metadata = Column(JSONB)  # For storing structured insight data (renamed from 'metadata' - reserved)
    source_conversations = Column(ARRAY(UUID))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    acknowledged = Column(Boolean, default=False)
