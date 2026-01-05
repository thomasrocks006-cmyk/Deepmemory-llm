# Learning Loop Architecture

## Overview

The Learning Loop is a continuous improvement system that extracts knowledge, detects conflicts, and generates insights automatically after each conversation turn.

## Core Components

### 1. Post-Turn Extraction

Runs after every assistant response to extract structured information.

```python
from app.learning_loop import LearningLoop

loop = LearningLoop(gemini_client, vector_db, graph_db)

result = await loop.post_turn_extraction(
    conversation_id="conv_123",
    message_id="msg_456",
    db=db_session
)
```

**Extracts:**
- Facts: Concrete user information
- Entities: People, places, concepts
- Sentiment: Emotional state
- Values: What matters to the user

**Output:**
```json
{
  "extracted": {
    "facts": ["User loves Python", "Works remotely"],
    "entities": [
      {"name": "Python", "type": "concept", "context": "programming"}
    ],
    "sentiment": {"valence": 80, "arousal": 60, "dominance": 70},
    "values": ["learning", "flexibility"]
  },
  "conflicts": [],
  "entities_added": 1
}
```

### 2. Conflict Detection

Identifies contradictions with existing knowledge.

```python
conflicts = await loop._detect_conflicts(
    new_facts=["I love working from home"],
    db=db_session
)
```

**Example Conflict:**
```json
{
  "fact": "I love working from home",
  "conflicts_with": "I prefer working in an office for collaboration",
  "explanation": "Contradictory preferences about work location",
  "severity": "moderate"
}
```

Conflicts are stored in database for later resolution.

### 3. Knowledge Graph Updates

Automatically adds entities and relationships to Neo4j.

```python
# Extracted entity is automatically added
await loop._update_knowledge_graph(
    entities=[{
        "name": "Python",
        "type": "concept",
        "context": "User's favorite programming language"
    }],
    message_id="msg_456",
    db=db_session
)
```

**Graph Structure:**
```
(Python:CONCEPT)-[:MENTIONED_IN]->(Message)
(User)-[:INTERESTED_IN]->(Python)
(Python)-[:RELATED_TO]->(MachineLearning)
```

### 4. Scratchpad Updates

Maintains a living document that evolves with conversation.

```python
await loop._update_scratchpad(
    conversation_id="conv_123",
    extracted={
        "facts": ["Learned about neural networks"],
        "values": ["deep understanding"],
        "sentiment": {"valence": 90}
    },
    db=db_session
)
```

**Scratchpad Example:**
```markdown
# Conversation Notes

## User Profile
- Name: Alice
- Interests: AI, Python, Philosophy
- Current Focus: Learning machine learning

## Key Topics
- Neural networks architecture
- Backpropagation algorithm
- Practical applications

## Emotional Tone
- Enthusiastic about learning
- Curious and asking deep questions
- Some anxiety about keeping up with field

## Goals
- Build first ML project
- Understand theory deeply
- Apply to career transition
```

### 5. Reflection Events

Periodic meta-analysis triggered every 5 turns.

```python
insights = await loop.reflection_event(
    conversation_id="conv_123",
    db=db_session
)
```

**Reflection Output:**
```json
{
  "patterns": [
    "User oscillates between theoretical and practical questions",
    "Growing confidence over time"
  ],
  "growth": "Started with basic concepts, now asking about advanced architectures",
  "opportunities": [
    "Explore transformers and attention mechanisms",
    "Discuss ethical implications of AI"
  ],
  "blind_spots": [
    "Not considering data quality and bias issues",
    "Focusing only on technical aspects, not business value"
  ]
}
```

### 6. Subconscious Agent

Background processing for deep pattern recognition.

```python
# Run nightly or on-demand
insights = await loop.subconscious_agent(
    db=db_session,
    lookback_days=7
)
```

**Deep Insights:**
```json
{
  "hidden_motivations": [
    "Seeking validation for career change decision",
    "Building confidence through mastery"
  ],
  "patterns": [
    "Questions cluster around uncertainty and competence",
    "Engages most deeply when discussing real-world applications"
  ],
  "emotional_themes": [
    "Imposter syndrome",
    "Excitement about new possibilities"
  ],
  "predicted_needs": [
    "Practical project guidance",
    "Community and mentorship connections",
    "Career transition roadmap"
  ]
}
```

### 7. Hierarchical Summarization

Compresses memory across tiers.

```python
# Tier 1: Last 100k tokens (detailed)
summary_1 = await loop.summarize_tier(
    conversation_id="conv_123",
    tier=1,
    db=db_session
)

# Tier 2: Compressed summary (key points)
summary_2 = await loop.summarize_tier(
    conversation_id="conv_123",
    tier=2,
    db=db_session
)

# Tier 3: Ultra-compressed (main themes)
summary_3 = await loop.summarize_tier(
    conversation_id="conv_123",
    tier=3,
    db=db_session
)
```

## Integration with FastAPI

```python
from app.main import app

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # ... generate response ...
    
    # Trigger post-turn extraction (background)
    import asyncio
    asyncio.create_task(
        app.state.learning_loop.post_turn_extraction(
            conversation_id=conv_id,
            message_id=msg_id,
            db=db
        )
    )
    
    # Reflection every 5 turns
    if message_count % 5 == 0:
        asyncio.create_task(
            app.state.learning_loop.reflection_event(
                conversation_id=conv_id,
                db=db
            )
        )
    
    return response
```

## Database Schema

### Conflicts Table
```sql
CREATE TABLE conflicts (
    id UUID PRIMARY KEY,
    statement_a TEXT NOT NULL,
    statement_b TEXT NOT NULL,
    explanation TEXT,
    severity VARCHAR(20),  -- minor, moderate, major
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Scratchpad Table
```sql
CREATE TABLE scratchpad (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Insights Table
```sql
CREATE TABLE insights (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    insight_type VARCHAR(50),  -- reflection, subconscious
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Performance Considerations

1. **Background Processing**: All extraction runs async to not block responses
2. **Batch Updates**: Group graph updates to reduce Neo4j calls
3. **Caching**: Cache recent extractions to avoid re-processing
4. **Rate Limiting**: Limit subconscious agent frequency

## Configuration

```python
# In config.py
class Settings(BaseSettings):
    # Learning loop settings
    reflection_frequency: int = 5  # turns
    subconscious_schedule: str = "0 2 * * *"  # 2 AM daily
    conflict_threshold: float = 0.85  # similarity threshold
    max_entities_per_turn: int = 10
```

## Monitoring

Track learning loop effectiveness:

```python
# Metrics to monitor
- Entities extracted per conversation
- Conflicts detected
- Reflection insights generated
- Scratchpad update frequency
- Processing time per turn
```

## Future Enhancements

1. **Active Conflict Resolution**: Prompt user when conflicts detected
2. **Insight Surfacing**: Proactively share insights during conversation
3. **Pattern-based Suggestions**: Suggest topics based on patterns
4. **Multi-user Profiles**: Link related personas across conversations
5. **Temporal Analysis**: Track how values/goals change over time

## Example Workflow

```
User Message
     ↓
Assistant Response
     ↓
Post-Turn Extraction (async)
     ├── Extract facts
     ├── Identify entities → Update graph
     ├── Analyze sentiment
     ├── Detect conflicts → Store if found
     └── Update scratchpad
     ↓
Check Turn Count
     ↓
If % 5 == 0: Reflection Event
     └── Generate meta-insights
     
Nightly: Subconscious Agent
     └── Deep pattern analysis
```

## Testing

```bash
# Test post-turn extraction
pytest tests/test_learning_loop.py::test_post_turn_extraction -v

# Test conflict detection
pytest tests/test_learning_loop.py::test_conflict_detection -v

# Test reflection
pytest tests/test_learning_loop.py::test_reflection_event -v
```

## Resources

- See `backend/app/learning_loop.py` for implementation
- See `tests/test_learning_loop.py` for examples
- See `IMPLEMENTATION_PLAN.md` for architecture overview
