# DeepMemory LLM - Quick Start Guide

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11 or higher
- [ ] PostgreSQL 15+ with pgvector extension
- [ ] Neo4j 5+ (Community or Enterprise)
- [ ] Pinecone account with API key
- [ ] Google Cloud account with Gemini API access
- [ ] Node.js 18+ (for frontend, later)

## Step-by-Step Setup

### 1. Install PostgreSQL with pgvector

**Ubuntu/Debian:**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install pgvector extension
sudo apt install postgresql-15-pgvector

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql@15
brew install pgvector
brew services start postgresql@15
```

**Create Database:**
```bash
# Access PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE deepmemory;
CREATE USER deepmemory_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE deepmemory TO deepmemory_user;
\q

# Run schema
psql -U deepmemory_user -d deepmemory -f backend/database/schema.sql
```

### 2. Install Neo4j

**Ubuntu/Debian:**
```bash
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j

# Start Neo4j
sudo systemctl start neo4j
sudo systemctl enable neo4j
```

**macOS:**
```bash
brew install neo4j
brew services start neo4j
```

**Configure Neo4j:**
```bash
# Access Neo4j browser at http://localhost:7474
# Default credentials: neo4j / neo4j
# Change password on first login
```

### 3. Set Up Pinecone

1. Go to [Pinecone.io](https://www.pinecone.io)
2. Sign up for free account
3. Create a new project
4. Create an index with:
   - **Dimension:** 768
   - **Metric:** Cosine
   - **Cloud:** GCP
   - **Region:** us-west1 (or your preferred region)
5. Copy your API key

### 4. Get Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Enable Gemini API in your project
4. Copy the API key

### 5. Set Up Python Backend

```bash
# Clone repository
git clone https://github.com/thomasrocks006-cmyk/Deepmemory-llm.git
cd Deepmemory-llm/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 6. Configure Environment

```bash
# Copy example environment file
cp ../.env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Required variables to set:**
```env
# Google Gemini
GOOGLE_API_KEY=your_gemini_api_key_here

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=deepmemory-vectors

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# PostgreSQL
DATABASE_URL=postgresql://deepmemory_user:your_password@localhost:5432/deepmemory
```

### 7. Run the Backend

```bash
# From backend directory with venv activated
python -m uvicorn app.main:app --reload

# Server will start at http://localhost:8000
```

### 8. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "pinecone": "connected",
#   "neo4j": "connected",
#   "pinecone_vectors": 0
# }
```

## Using the API

### 1. Import Conversations

**ChatGPT Export:**
```bash
# Export your ChatGPT data from Settings > Data Controls > Export Data
# You'll receive a conversations.json file

curl -X POST http://localhost:8000/api/ingest \
  -F "files=@conversations.json"
```

**Gemini Export:**
```bash
# Export from Google Takeout > Gemini Activity
# Upload the exported files

curl -X POST http://localhost:8000/api/ingest \
  -F "files=@gemini_conversations.json"
```

**Manual Transcript:**
```bash
# Create a .txt or .md file with format:
# User: message
# Assistant: response
# User: next message
# Assistant: next response

curl -X POST http://localhost:8000/api/ingest \
  -F "files=@manual_transcript.txt"
```

### 2. Chat with Your Memory

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did I discuss with Jordy about the app?",
    "conversation_history": []
  }'
```

### 3. View Psychological Profiles

```bash
# Get profile for a person
curl http://localhost:8000/api/profiles/Ella

# Manually update a profile
curl -X POST http://localhost:8000/api/profiles/Ella/update \
  -H "Content-Type: application/json" \
  -d '{
    "recent_turns": [
      {"role": "user", "content": "Ella seems stressed about the timeline"}
    ]
  }'
```

## Troubleshooting

### PostgreSQL Connection Error

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
psql -U postgres -l | grep deepmemory

# Test connection
psql "postgresql://deepmemory_user:your_password@localhost:5432/deepmemory"
```

### Neo4j Connection Error

```bash
# Check if Neo4j is running
sudo systemctl status neo4j

# Check logs
sudo journalctl -u neo4j -n 50

# Verify connection
curl http://localhost:7474
```

### Pinecone Index Not Found

```bash
# Verify index name matches .env
# Check Pinecone dashboard: https://app.pinecone.io

# The index will be created automatically on first run
# Check logs for any creation errors
```

### Gemini API Error

```bash
# Verify API key is correct
# Check quota limits in Google Cloud Console
# Ensure Gemini API is enabled
```

## Next Steps

1. **Import Your Conversations**: Start with a small batch to test the system
2. **Monitor Logs**: Watch the console for any errors during ingestion
3. **Query Your Memory**: Test the chat endpoint with various questions
4. **Review Profiles**: Check the psychological profiles being generated
5. **Iterate**: Provide feedback and refine the system

## Development Workflow

```bash
# Always activate virtual environment first
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Run in development mode (auto-reload)
python -m uvicorn app.main:app --reload --log-level debug

# Run tests (when available)
pytest

# Format code
black app/
ruff check app/
```

## Production Deployment

See [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) for production deployment guide with:
- Docker containerization
- Google Cloud Run deployment
- Environment security
- Monitoring and logging
- Backup strategies

## Support

- **Issues**: [GitHub Issues](https://github.com/thomasrocks006-cmyk/Deepmemory-llm/issues)
- **Docs**: [Implementation Plan](../IMPLEMENTATION_PLAN.md)
- **Updates**: Check commit history for latest features

---

**Current Phase**: Foundation Complete (Week 1-4) ✅  
**Next Milestone**: Frontend Development (Week 11-12)
