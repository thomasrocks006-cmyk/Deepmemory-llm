# DeepMemory LLM

> A next-generation LLM application with infinite context memory, psychological profiling, and lateral thinking capabilities.

## Project Status

✅ **Core Features Complete** - Ready for testing and refinement

### Completed (Weeks 1-16)

- ✅ Foundation & Data Architecture
- ✅ Multi-Agent System (Librarian, Strategist, Profiler)
- ✅ Data Ingestion Pipeline (ChatGPT, Gemini, Manual)
- ✅ Full API Implementation
- ✅ Next.js Frontend with Real-time Chat
- ✅ Learning Loop & Continuous Improvement
- ✅ Comprehensive Test Suite

### Next Steps

- 🔄 User Acceptance Testing
- 🔄 Performance Optimization
- 🔄 Production Deployment

## Overview

DeepMemory LLM transcends traditional context limitations by combining:
- **Infinite Memory**: Hierarchical compression for 10M+ token functional memory
- **Pedantic Retrieval**: Multi-dimensional vector search + knowledge graph
- **Psychological Profiling**: Deep, theory-driven analysis of people in your network
- **Lateral Thinking**: Finds "unrelated but useful" connections across conversations
- **Continuous Learning**: Every interaction improves the system

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│  Chat Interface • Folder Manager • Persona Cards        │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│                 Backend API (FastAPI)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Librarian │  │Strategist│  │ Profiler │  Agents     │
│  │  Agent   │  │  Agent   │  │  Agent   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────┬────────────┬────────────┬────────────────────────┘
      │            │            │
┌─────┴────┐  ┌───┴───┐  ┌────┴─────┐
│PostgreSQL│  │Pinecone│  │  Neo4j   │  Data Layer
│ +pgvector│  │ Vector │  │  Graph   │
└──────────┘  └────────┘  └──────────┘
```

## Technology Stack

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy + PostgreSQL (pgvector)
- Pinecone (vector search)
- Neo4j (knowledge graph)
- Google Gemini 3 Pro

**Frontend:**
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (with pgvector extension)
- Neo4j 5+
- Pinecone account
- Google Cloud account (Gemini API access)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/thomasrocks006-cmyk/Deepmemory-llm.git
   cd Deepmemory-llm
   ```

2. **Set up backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database credentials
   ```

4. **Initialize databases**
   ```bash
   # PostgreSQL
   psql -U postgres -f database/schema.sql
   
   # Neo4j constraints will be created automatically on first run
   ```

5. **Run the backend**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

6. **Set up frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Visit http://localhost:3000 to access the application!

## Project Structure

```
Deepmemory-llm/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration management
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── database.py          # Database connection
│   │   ├── gemini_client.py     # Gemini API client
│   │   ├── vector_db.py         # Pinecone client
│   │   ├── graph_db.py          # Neo4j client
│   │   ├── learning_loop.py     # Learning & reflection system
│   │   ├── agents/              # AI agents
│   │   │   ├── base_agent.py
│   │   │   ├── librarian.py     # Retrieval specialist
│   │   │   ├── strategist.py    # User-facing advisor
│   │   │   └── profiler.py      # Psychological analyst
│   │   └── ingestion/           # Data importers
│   │       ├── orchestrator.py
│   │       ├── chatgpt_importer.py
│   │       ├── gemini_importer.py
│   │       ├── manual_importer.py
│   │       └── coreference.py
│   ├── database/
│   │   └── schema.sql           # PostgreSQL schema
│   ├── tests/                   # Comprehensive test suite
│   │   ├── conftest.py
│   │   ├── test_agents.py
│   │   ├── test_ingestion.py
│   │   ├── test_learning_loop.py
│   │   └── test_api.py
│   ├── requirements.txt
│   └── requirements-test.txt
├── frontend/                    # Next.js application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── FolderManager.tsx
│   │   │   ├── PersonaCards.tsx
│   │   │   └── MemoryPanel.tsx
│   │   ├── lib/
│   │   │   └── api.ts
│   │   └── store/
│   │       └── chat.ts
│   ├── package.json
│   └── tsconfig.json
├── IMPLEMENTATION_PLAN.md       # Detailed implementation guide
├── QUICKSTART.md                # Quick setup guide
├── TESTING.md                   # Testing documentation
├── FRONTEND.md                  # Frontend development guide
├── LEARNING_LOOP.md             # Learning loop architecture
└── README.md
```

## Development Roadmap

- [x] **Week 1-2**: Foundation & Data Architecture
  - [x] Database schemas (PostgreSQL, Neo4j)
  - [x] Vector database setup (Pinecone)
  - [x] Core clients (Gemini, databases)
  - [x] Basic ingestion scripts
  
- [x] **Week 3-4**: Data Ingestion Pipeline
  - [x] ChatGPT parser
  - [x] Gemini parser (JSON + HTML)
  - [x] Manual transcript parser
  - [x] Coreference resolution
  - [x] Orchestration layer

- [x] **Week 5-8**: Multi-Agent Architecture
  - [x] Librarian Agent (retrieval)
  - [x] Strategist Agent (user-facing)
  - [x] Profiler Agent (psychological)
  - [x] Multi-vector search
  - [x] Knowledge graph traversal
  
- [x] **Week 9-10**: API & Integration
  - [x] Chat endpoints
  - [x] Ingest endpoints
  - [x] Profile endpoints
  - [x] Agent integration
  
- [x] **Week 11-12**: Frontend Development
  - [x] Next.js setup
  - [x] Chat interface
  - [x] Folder manager
  - [x] Persona cards
  - [x] Memory panel
  - [x] API integration
  
- [x] **Week 13-14**: Learning Loop
  - [x] Post-turn extraction
  - [x] Conflict detection
  - [x] Scratchpad updates
  - [x] Reflection events
  - [x] Subconscious agent
  - [x] Hierarchical summarization
  
- [x] **Week 15-16**: Testing & Refinement
  - [x] Unit tests
  - [x] Integration tests
  - [x] Agent tests
  - [x] API tests
  - [x] Test fixtures
  
- [ ] **Week 17+**: Production Deployment
  - [ ] Docker containerization
  - [ ] CI/CD pipeline
  - [ ] Monitoring & logging
  - [ ] Performance optimization
  - [ ] Security hardening
  - [ ] Monitoring & logging
  - [ ] Performance optimization
  - [ ] Security hardening

## API Endpoints

### Health & Status
- `GET /health` - Health check

### Chat
- `POST /api/chat` - Main chat endpoint with multi-agent processing
- `WebSocket /ws/chat` - Real-time streaming (future)

### Data Management
- `POST /api/ingest` - Import conversations (ChatGPT, Gemini, Manual)

### Profiles
- `GET /api/profiles` - List all personas
- `GET /api/profiles/{person}` - Get detailed psychological profile

### Memory (Future)
- `GET /api/memory/stats` - Memory tier statistics
- `GET /api/profiles/{person_name}` - Get psychological profile
- `POST /api/profiles/{person_name}/update` - Trigger profile update

## Testing

Run the comprehensive test suite:

```bash
cd backend

# Install test dependencies
pip install -r requirements-test.txt

# Run all tests with coverage
bash run_tests.sh

# Or run specific test categories
pytest tests/ -m unit -v          # Unit tests only
pytest tests/ -m integration -v   # Integration tests
pytest tests/ -m agent -v         # Agent tests
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Configuration

Key environment variables (see `.env.example`):

```env
# Google Gemini
GOOGLE_API_KEY=your_api_key

# Pinecone
PINECONE_API_KEY=your_api_key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=deepmemory

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/deepmemory

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Detailed implementation plan
- [TESTING.md](TESTING.md) - Testing guide
- [FRONTEND.md](FRONTEND.md) - Frontend development guide
- [LEARNING_LOOP.md](LEARNING_LOOP.md) - Learning loop architecture

## Key Features

### Infinite Context Memory
- **Tier 1**: Last 100k tokens in active context
- **Tier 2**: Up to 1M tokens in Gemini cache
- **Tier 3**: Unlimited in vector database + knowledge graph
- **Tier 4**: Hierarchical summarization for compression

### Multi-Agent System
- **Librarian**: Deep retrieval with multi-vector search + GraphRAG
- **Strategist**: User-facing responses with context synthesis
- **Profiler**: Psychological analysis using Big Five + SDT + Maslow

### Learning Loop
- **Post-Turn Extraction**: Automatic fact and entity extraction
- **Conflict Detection**: Identifies contradictions in knowledge
- **Reflection Events**: Generates meta-insights every 5 turns
- **Subconscious Agent**: Background pattern recognition
- **Scratchpad**: Living document that evolves with conversation

### Data Ingestion
- **ChatGPT**: Parses conversations.json exports
- **Gemini**: Handles JSON and HTML from Google Takeout
- **Manual**: Processes plain text transcripts
- **Coreference Resolution**: Resolves pronouns to entity names

## Contributing

This is a personal project currently in active development. Contributions, suggestions, and feedback are welcome!

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with insights from:
- Google Gemini 3 Pro Preview
- Neo4j knowledge graph patterns
- Pinecone vector search best practices
- FastAPI and Next.js communities

---

**Current Phase**: Testing & Refinement (Week 15-16)  
**Next Milestone**: Production Deployment (Week 17+)
