"""
FastAPI main application.
Entry point for the DeepMemory LLM backend.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import uvicorn

from app.config import get_settings
from app.database import init_db, get_db_session
from app.gemini_client import gemini_client
from app.llama_embeddings import get_llama_client
from app.vector_db import pinecone_client
from app.graph_db import neo4j_client
from app.agents import LibrarianAgent, StrategistAgent, ProfilerAgent
from app.agents.validator import ValidatorAgent
from app.ingestion import ingestion_orchestrator
from app.learning_loop import LearningLoop

# Initialize embedding client
embedding_client = get_llama_client()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="DeepMemory LLM API",
    description="Long-context memory LLM with psychological profiling and lateral thinking",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and connections on startup."""
    logger.info("Starting DeepMemory LLM API...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Create Neo4j constraints
    try:
        neo4j_client.create_constraints()
        logger.info("Neo4j constraints created")
    except Exception as e:
        logger.warning(f"Neo4j initialization failed: {e}")
    
    # Check Pinecone connection (non-blocking)
    try:
        stats = pinecone_client.get_index_stats()
        logger.info(f"Pinecone index stats: {stats}")
    except Exception as e:
        logger.warning(f"Pinecone initialization failed: {e}")
        logger.info("App will continue without Pinecone (vector search disabled)")
    
    # Initialize AI agents
    app.state.librarian = LibrarianAgent()
    app.state.strategist = StrategistAgent()
    app.state.profiler = ProfilerAgent()
    app.state.validator = ValidatorAgent()
    logger.info("AI agents initialized")
    
    # Initialize learning loop
    app.state.learning_loop = LearningLoop(gemini_client, pinecone_client, neo4j_client)
    logger.info("Learning loop initialized")
    
    logger.info("DeepMemory LLM API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down DeepMemory LLM API...")
    neo4j_client.close()
    logger.info("Connections closed")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "DeepMemory LLM API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    try:
        # Check database using context manager
        from app.database import get_db
        from sqlalchemy import text
        with get_db() as db:
            db.execute(text("SELECT 1"))
        
        # Check Pinecone
        pinecone_stats = pinecone_client.get_index_stats()
        
        # Check Neo4j
        with neo4j_client.driver.session() as session:
            session.run("RETURN 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "pinecone": "connected",
            "neo4j": "connected",
            "pinecone_vectors": pinecone_stats.get("total_vector_count", 0)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# Placeholder routes (to be implemented in later stages)

@app.post("/api/chat")
async def chat_endpoint(request: Dict[str, Any], db: Session = Depends(get_db_session)):
    """
    Main chat endpoint with multi-agent processing.
    
    Request body:
    {
        "query": "user question",
        "message": "alternative field name",
        "conversation_id": "optional conversation id",
        "conversation_history": [...previous turns...]
    }
    """
    try:
        # Support both 'query' and 'message' field names for flexibility
        query = request.get("query") or request.get("message", "")
        history = request.get("conversation_history", [])
        conversation_id = request.get("conversation_id", "default")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query or message is required")
        
        # Step 1: Librarian prepares context
        context_brief = await app.state.librarian.process({
            "query": query,
            "filters": {}
        })
        
        # Step 2: Profiler gets relevant personas
        personas = await app.state.profiler.get_relevant_profiles(query)
        
        # Step 3: Strategist generates response
        response = await app.state.strategist.process({
            "query": query,
            "context_brief": context_brief,
            "personas": personas,
            "conversation_history": history
        })
        
        # Trigger post-turn extraction (background task)
        import asyncio
        asyncio.create_task(
            app.state.learning_loop.post_turn_extraction(
                conversation_id=conversation_id,
                message_id="temp_id",  # Would be from database
                db=db
            )
        )
        
        # Check if reflection needed (every 5 turns)
        # In production, track this in database
        if len(history) % 5 == 0 and len(history) > 0:
            asyncio.create_task(
                app.state.learning_loop.reflection_event(
                    conversation_id=conversation_id,
                    db=db
                )
            )
        
        return {
            "status": "success",
            "role": "assistant",
            "content": response['content'],
            "response": response['content'],
            "thinking": response.get('thinking'),
            "sources": response.get('sources', []),
            "metadata": response.get('metadata', {})
        }
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest")
async def ingest_conversations(files: List[UploadFile] = File(...)):
    """
    Conversation ingestion endpoint.
    
    Accepts conversation exports from ChatGPT, Gemini, Grok, or manual transcripts.
    """
    try:
        results = []
        
        for file in files:
            # Detect source type from filename or content
            filename = file.filename or "unknown"
            source_type = detect_source_type(filename)
            
            # Read file content
            content = await file.read()
            
            # Process through ingestion orchestrator
            report = await ingestion_orchestrator.ingest_file(
                file_content=content,
                source_type=source_type,
                filename=filename
            )
            
            results.append(report)
        
        return {
            "status": "success",
            "files_processed": len(files),
            "reports": results
        }
        
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def detect_source_type(filename: str) -> str:
    """Detect conversation source from filename."""
    filename_lower = filename.lower()
    
    if 'chatgpt' in filename_lower or 'conversations.json' in filename_lower:
        return 'chatgpt'
    elif 'gemini' in filename_lower or 'takeout' in filename_lower:
        return 'gemini'
    elif 'grok' in filename_lower:
        return 'grok'
    else:
        return 'manual'


@app.get("/api/conversations")
async def list_conversations(db: Session = Depends(get_db_session), limit: int = 50):
    """List all uploaded conversations."""
    try:
        from app.models import Conversation
        conversations = db.query(Conversation).order_by(Conversation.ingestion_date.desc()).limit(limit).all()
        return {
            "status": "success",
            "conversations": [
                {
                    "id": str(c.id),
                    "title": c.title or f"Conversation from {c.source}",
                    "source": c.source,
                    "total_messages": c.total_messages,
                    "ingestion_date": c.ingestion_date.isoformat() if c.ingestion_date else None,
                    "importance_score": c.importance_score
                }
                for c in conversations
            ],
            "total": len(conversations)
        }
    except Exception as e:
        logger.error(f"Conversation listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles")
async def list_profiles(db: Session = Depends(get_db_session)):
    """List all persona profiles."""
    try:
        from app.models import Persona
        personas = db.query(Persona).all()
        return {
            "status": "success",
            "personas": [p.person_name for p in personas]
        }
    except Exception as e:
        logger.error(f"Profile listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles/{person_name}")
async def get_persona_profile(person_name: str):
    """Get psychological profile for a person."""
    try:
        profile = await app.state.profiler.get_profile(person_name)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile not found for {person_name}")
        
        return {
            "status": "success",
            "person_name": person_name,
            "profile": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profiles/{person_name}/update")
async def trigger_profile_update(person_name: str, request: Optional[Dict[str, Any]] = None):
    """Manually trigger a profile update."""
    try:
        recent_turns = request.get("recent_turns", []) if request else []
        
        await app.state.profiler.reflection_event(person_name, recent_turns)
        
        return {
            "status": "success",
            "message": f"Profile update triggered for {person_name}"
        }
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/stats")
async def get_memory_stats(db: Session = Depends(get_db_session)):
    """Get memory usage statistics."""
    try:
        from app.models import Conversation, Message, Persona
        
        total_conversations = db.query(Conversation).count()
        total_messages = db.query(Message).count()
        total_personas = db.query(Persona).count()
        
        # Get Pinecone stats (gracefully handle errors)
        try:
            pinecone_stats = pinecone_client.get_index_stats()
        except Exception:
            pinecone_stats = {'total_vector_count': 0}
        
        return {
            "status": "success",
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_personas": total_personas,
            "memory_tiers": {
                "tier1_size": total_messages,  # Approximate
                "tier2_size": pinecone_stats.get("total_vector_count", 0),
                "tier3_size": pinecone_stats.get("total_vector_count", 0)
            }
        }
    except Exception as e:
        logger.error(f"Memory stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== VALIDATION ENDPOINTS =====

@app.post("/api/validate/documents")
async def validate_documents(
    documents: List[Dict[str, Any]],
    check_against_existing: bool = True
):
    """
    Validate documents for contradictions and hallucinations before ingestion.
    
    This is the "Check for Discrepancies" button functionality.
    
    Request body:
    {
        "documents": [
            {
                "id": "doc_1",
                "content": "full text content...",
                "metadata": {...}
            }
        ],
        "check_against_existing": true
    }
    
    Returns validation report with all detected issues.
    """
    try:
        logger.info(f"Validating {len(documents)} documents")
        
        # Run validation through Validator agent
        report = await app.state.validator.validate_documents(
            documents=documents,
            check_against_existing=check_against_existing
        )
        
        return {
            "status": "success",
            "report": report
        }
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/validate/conflicts")
async def get_unresolved_conflicts(db: Session = Depends(get_db_session)):
    """Get all unresolved conflicts from the database."""
    try:
        from app.models import Conflict
        from sqlalchemy import select
        
        conflicts = db.execute(
            select(Conflict).where(Conflict.resolved == False)
        ).fetchall()
        
        conflict_list = []
        for row in conflicts:
            conflict = row[0]
            conflict_list.append({
                "id": str(conflict.id),
                "type": conflict.conflict_type,
                "severity": conflict.severity,
                "statement_a": conflict.statement_a or conflict.old_value,
                "statement_b": conflict.statement_b or conflict.new_value,
                "explanation": conflict.explanation,
                "detected_at": conflict.detected_at.isoformat() if conflict.detected_at else None
            })
        
        return {
            "status": "success",
            "total_conflicts": len(conflict_list),
            "conflicts": conflict_list
        }
        
    except Exception as e:
        logger.error(f"Get conflicts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/validate/resolve/{conflict_id}")
async def resolve_conflict(
    conflict_id: str,
    resolution: str,
    correct_value: Optional[str] = None
):
    """
    Mark a conflict as resolved with user's decision.
    
    Request body:
    {
        "resolution": "User's explanation of how this was resolved",
        "correct_value": "The correct value if applicable"
    }
    """
    try:
        success = await app.state.validator.resolve_conflict(
            conflict_id=conflict_id,
            resolution=resolution,
            correct_value=correct_value
        )
        
        if success:
            return {
                "status": "success",
                "message": "Conflict resolved"
            }
        else:
            raise HTTPException(status_code=404, detail="Conflict not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resolve conflict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket chat endpoint (to be implemented)."""
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "system",
            "content": "WebSocket connection established (implementation coming soon)"
        })
        
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({
                "type": "system",
                "content": "Echo: " + str(data)
            })
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
