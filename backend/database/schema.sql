-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(20) NOT NULL CHECK (source IN ('chatgpt', 'gemini', 'grok', 'manual')),
    title TEXT,
    date_range TSTZRANGE,
    total_messages INTEGER,
    ingestion_date TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    importance_score INTEGER DEFAULT 5 CHECK (importance_score BETWEEN 1 AND 10)
);

-- Messages table with vector embeddings
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    resolved_content TEXT,
    timestamp TIMESTAMPTZ,
    
    -- Multi-dimensional embeddings
    semantic_embedding vector(1024),
    sentiment_embedding vector(1024),
    strategic_embedding vector(1024),
    
    metadata JSONB,
    entities TEXT[]
);

-- Personas (psychological profiles)
CREATE TABLE IF NOT EXISTS personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_name VARCHAR(255) UNIQUE NOT NULL,
    profile JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    first_mentioned TIMESTAMPTZ,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    total_references INTEGER DEFAULT 0,
    previous_versions JSONB[]
);

-- Hierarchical summaries
CREATE TABLE IF NOT EXISTS summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level VARCHAR(10) NOT NULL CHECK (level IN ('L0_Raw', 'L1_Session', 'L2_Project', 'L3_Identity')),
    scope_id UUID,
    summary_text TEXT NOT NULL,
    token_count INTEGER,
    compression_ratio DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conflict tracking
CREATE TABLE IF NOT EXISTS conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50),
    entity_id UUID,
    conflict_type VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolution TEXT
);

-- Scratchpad (living document)
CREATE TABLE IF NOT EXISTS scratchpad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

-- Proactive insights
CREATE TABLE IF NOT EXISTS insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    insight_type VARCHAR(50) CHECK (insight_type IN ('pattern', 'conflict', 'suggestion', 'cross_pollination')),
    title VARCHAR(255),
    content TEXT NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    source_conversations UUID[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged BOOLEAN DEFAULT FALSE
);

-- Indexes for performance

-- Vector similarity search indexes (using IVFFlat)
CREATE INDEX IF NOT EXISTS messages_semantic_idx ON messages 
    USING ivfflat (semantic_embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS messages_sentiment_idx ON messages 
    USING ivfflat (sentiment_embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS messages_strategic_idx ON messages 
    USING ivfflat (strategic_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Standard indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_entities ON messages USING GIN(entities);
CREATE INDEX IF NOT EXISTS idx_conversations_source ON conversations(source);
CREATE INDEX IF NOT EXISTS idx_conversations_date_range ON conversations USING GIST(date_range);
CREATE INDEX IF NOT EXISTS idx_personas_name ON personas(person_name);
CREATE INDEX IF NOT EXISTS idx_summaries_level ON summaries(level);
CREATE INDEX IF NOT EXISTS idx_conflicts_resolved ON conflicts(resolved);
CREATE INDEX IF NOT EXISTS idx_insights_user ON insights(user_id);
CREATE INDEX IF NOT EXISTS idx_insights_acknowledged ON insights(acknowledged);

-- JSONB indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_conversations_metadata ON conversations USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_messages_metadata ON messages USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_personas_profile ON personas USING GIN(profile);

-- Comments for documentation
COMMENT ON TABLE conversations IS 'Stores metadata about imported conversation threads';
COMMENT ON TABLE messages IS 'Individual messages with multi-dimensional vector embeddings for semantic search';
COMMENT ON TABLE personas IS 'Psychological profiles of people mentioned in conversations';
COMMENT ON TABLE summaries IS 'Hierarchical summaries at different compression levels (L1-L3)';
COMMENT ON TABLE conflicts IS 'Tracks contradictions in data requiring resolution';
COMMENT ON TABLE scratchpad IS 'Living document summarizing current state (Tier 1 memory)';
COMMENT ON TABLE insights IS 'Proactive insights generated by subconscious agent';
