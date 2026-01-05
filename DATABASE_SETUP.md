# Database Setup Guide

## 🎯 Quick Status

All databases are running locally in Docker containers and ready for development.

## 📊 PostgreSQL (with pgvector)

**Connection Details:**
- Host: `localhost`
- Port: `5432`
- Database: `deepmemory`
- Username: `deepmemory`
- Password: `deepmemory_password`

**Features:**
- ✅ pgvector extension (v0.8.1) for vector embeddings
- ✅ pg_trgm for text search
- ✅ btree_gin for array indexes
- ✅ 7 tables initialized (conversations, messages, personas, summaries, conflicts, scratchpad, insights)

**Management Commands:**
```bash
# View logs
docker logs deepmemory-postgres

# Connect with psql
docker exec -it deepmemory-postgres psql -U deepmemory -d deepmemory

# Stop container
docker stop deepmemory-postgres

# Start container
docker start deepmemory-postgres

# Restart container
docker restart deepmemory-postgres
```

## 🕸️ Neo4j Graph Database

**Connection Details:**
- Bolt URI: `bolt://localhost:7687`
- HTTP UI: `http://localhost:7474`
- Username: `neo4j`
- Password: `deepmemory_neo4j`

**Features:**
- ✅ APOC plugin installed (436 procedures)
- ✅ Community Edition v5.15
- ✅ Ready for knowledge graph operations

**Management Commands:**
```bash
# View logs
docker logs deepmemory-neo4j

# Access Cypher shell
docker exec -it deepmemory-neo4j cypher-shell -u neo4j -p deepmemory_neo4j

# Stop container
docker stop deepmemory-neo4j

# Start container
docker start deepmemory-neo4j

# Restart container
docker restart deepmemory-neo4j
```

**Access Neo4j Browser:**
1. Open `http://localhost:7474` in your browser
2. Connect URI: `bolt://localhost:7687`
3. Username: `neo4j`
4. Password: `deepmemory_neo4j`

## 🐳 Docker Compose File

The databases are managed by a Docker Compose file at `/tmp/docker-compose-databases.yml`:

```bash
# Start all databases
cd /tmp && docker-compose -f docker-compose-databases.yml up -d

# Stop all databases
cd /tmp && docker-compose -f docker-compose-databases.yml down

# View status
docker-compose -f /tmp/docker-compose-databases.yml ps

# Stop and remove with volumes (⚠️ deletes data)
docker-compose -f /tmp/docker-compose-databases.yml down -v
```

## 🔧 Initialization Scripts

### PostgreSQL Schema Initialization
```bash
cd /workspaces/Deepmemory-llm/backend
python3 << 'PYTHON'
from app.database import init_db
init_db()
print("✅ PostgreSQL schema initialized")
PYTHON
```

### Neo4j Constraints Setup
```bash
cd /workspaces/Deepmemory-llm/backend
python3 << 'PYTHON'
from app.graph_db import Neo4jClient
client = Neo4jClient()
client.create_constraints()
print("✅ Neo4j constraints created")
PYTHON
```

## 🧪 Test Connections

### Test PostgreSQL
```bash
cd /workspaces/Deepmemory-llm/backend
python3 << 'PYTHON'
import psycopg2
conn = psycopg2.connect(
    dbname="deepmemory",
    user="deepmemory",
    password="deepmemory_password",
    host="localhost",
    port="5432"
)
print("✅ PostgreSQL connection successful")
conn.close()
PYTHON
```

### Test Neo4j
```bash
cd /workspaces/Deepmemory-llm/backend
python3 << 'PYTHON'
from neo4j import GraphDatabase
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "deepmemory_neo4j")
)
with driver.session() as session:
    result = session.run("RETURN 1 AS test")
    assert result.single()["test"] == 1
print("✅ Neo4j connection successful")
driver.close()
PYTHON
```

## 📝 Environment Variables

The `.env` file has been updated with the correct credentials:

```env
# Neo4j Graph Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=deepmemory_neo4j

# PostgreSQL Database
DATABASE_URL=postgresql://deepmemory:deepmemory_password@localhost:5432/deepmemory
```

## 🚨 Troubleshooting

### PostgreSQL won't start
```bash
# Check if port 5432 is already in use
lsof -i :5432

# View logs for errors
docker logs deepmemory-postgres

# Remove and recreate
docker rm -f deepmemory-postgres
docker run -d --name deepmemory-postgres \
  -e POSTGRES_DB=deepmemory \
  -e POSTGRES_USER=deepmemory \
  -e POSTGRES_PASSWORD=deepmemory_password \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### Neo4j won't start
```bash
# Check if ports are in use
lsof -i :7474
lsof -i :7687

# View logs
docker logs deepmemory-neo4j

# Restart with fresh data
docker rm -f deepmemory-neo4j
docker volume rm tmp_neo4j_data tmp_neo4j_logs
# Then restart with docker-compose
```

### Connection refused errors
- Ensure containers are running: `docker ps`
- Check container health: `docker inspect deepmemory-postgres | grep Health`
- Verify network: `docker network ls`

## 📦 Data Volumes

Data is persisted in Docker volumes:
- `tmp_postgres_data` - PostgreSQL data
- `tmp_neo4j_data` - Neo4j graph data
- `tmp_neo4j_logs` - Neo4j logs

**View volumes:**
```bash
docker volume ls | grep tmp
```

**Backup data:**
```bash
# PostgreSQL backup
docker exec deepmemory-postgres pg_dump -U deepmemory deepmemory > backup.sql

# Neo4j backup
docker exec deepmemory-neo4j neo4j-admin database dump neo4j --to-path=/dumps
```

## ✨ Ready for Development!

Both databases are now running and initialized. You can start the FastAPI application:

```bash
cd /workspaces/Deepmemory-llm/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
