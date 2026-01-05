"""
Librarian Agent - Deep retrieval specialist.
Responsible for GraphRAG traversal and context preparation.
"""

from typing import Dict, Any, List, Optional
from app.agents.base_agent import BaseAgent
from app.vector_db import pinecone_client
from app.graph_db import neo4j_client
from app.gemini_client import gemini_client
from app.llama_embeddings import get_llama_client
import logging

logger = logging.getLogger(__name__)


LIBRARIAN_SYSTEM_PROMPT = """
You are a Senior Research Librarian with expertise in forensic analysis and lateral thinking.

Your ONLY task: Given a user query, prepare the PERFECT context package from the database.

Instructions:

1. **Multi-Vector Search:** Query across:
   - Semantic similarity (vector DB)
   - Relationship graphs (Neo4j traversal)
   - Temporal clustering (find conversations before/after key events)
   - Sentiment matching (find similar emotional states)

2. **Lateral Retrieval:** Don't just find exact matches. Ask:
   - "What past experiences (regardless of topic) share psychological parallels?"
   - "Who in the user's network might have relevant insights, even if not explicitly mentioned?"
   - "Are there contradictions in the database that need flagging?"

3. **Evidence Tracing:** For every fact retrieved, cite:
   - Source conversation ID
   - Exact timestamp
   - Surrounding context (3 messages before/after)

4. **Output Format:** Return a "Context Brief" (max 200k tokens) containing:
   - Direct matches (20%)
   - Lateral connections (30%)
   - Relationship maps (20%)
   - Contradictions/conflicts (10%)
   - Temporal context (20%)

Constraint: NO hallucination. Mark missing data as [INSUFFICIENT_DATA].
"""


class LibrarianAgent(BaseAgent):
    """
    The Librarian Agent performs deep retrieval and context preparation.
    It never talks to the user directly - only prepares context for the Strategist.
    """
    
    def __init__(self):
        super().__init__(
            name="Librarian",
            system_instruction=LIBRARIAN_SYSTEM_PROMPT
        )
        self.vector_db = pinecone_client
        self.graph_db = neo4j_client
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare comprehensive context for a user query.
        
        Args:
            input_data: Dict with 'query' and optional 'filters'
            
        Returns:
            Context brief with retrieved information
        """
        query = input_data.get("query", "")
        filters = input_data.get("filters", {})
        
        self.log_action("Starting context preparation", {"query_length": len(query)})
        
        # Step 1: Extract entities from query
        entities = await self._extract_entities(query)
        
        # Step 2: Multi-dimensional vector search
        vector_results = await self._multi_vector_search(query, filters)
        
        # Step 3: Graph traversal for relationships
        graph_results = await self._graph_traversal(entities)
        
        # Step 4: Hybrid re-ranking
        ranked_results = self._rerank_results(vector_results, graph_results)
        
        # Step 5: Generate context brief
        context_brief = await self._generate_context_brief(
            query=query,
            results=ranked_results,
            entities=entities
        )
        
        self.log_action("Context preparation complete", {
            "entities_found": len(entities),
            "vector_hits": len(vector_results),
            "graph_nodes": len(graph_results)
        })
        
        return context_brief
    
    async def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities from the query using deep analysis."""
        extraction_prompt = f"""
        Analyze this query and extract all named entities with contextual understanding:
        - People names (and their relationships)
        - Project names
        - Concepts/topics (including implied subjects)
        - Locations
        
        Query: {query}
        
        Return a JSON array of entity names. Use lateral thinking to identify entities
        that might be relevant even if not explicitly named.
        """
        
        # Use Pro model with thinking for deeper entity extraction
        response = await self.generate_response(
            prompt=extraction_prompt,
            thinking_level="medium",
            temperature="conservative"
        )
        
        try:
            import json
            entities = json.loads(response['response'])
            return entities if isinstance(entities, list) else []
        except:
            return []
    
    async def _multi_vector_search(
        self,
        query: str,
        filters: Dict[str, Any]
    ) -> List[Dict]:
        """
        Perform multi-dimensional vector search.
        
        Searches across semantic, sentiment, strategic, and temporal dimensions.
        """
        # Get Llama embedding client
        llama_client = get_llama_client()
        
        # Generate embeddings for each dimension
        semantic_emb = llama_client.embed_text(query, task_type="retrieval_query")
        
        sentiment_emb = await llama_client.create_specialized_embedding(
            query, "sentiment"
        )
        
        strategic_emb = await llama_client.create_specialized_embedding(
            query, "strategic"
        )
        
        # Query across dimensions
        results = self.vector_db.multi_dimensional_query(
            query_embeddings={
                'semantic': semantic_emb,
                'sentiment': sentiment_emb,
                'strategic': strategic_emb
            },
            top_k=50,
            weights={
                'semantic': 0.4,
                'sentiment': 0.3,
                'strategic': 0.3
            }
        )
        
        return results
    
    async def _graph_traversal(self, entities: List[str]) -> List[Dict]:
        """
        Traverse the knowledge graph starting from extracted entities.
        """
        all_results = []
        
        for entity in entities:
            try:
                # Traverse relationships
                connected = self.graph_db.traverse_graph(
                    start_node=entity,
                    max_depth=3,
                    relationship_types=['KNOWS', 'WORKS_ON', 'RELATES_TO', 'MENTIONED_IN']
                )
                all_results.extend(connected)
            except Exception as e:
                logger.warning(f"Graph traversal failed for {entity}: {e}")
        
        return all_results
    
    def _rerank_results(
        self,
        vector_results: List[Dict],
        graph_results: List[Dict]
    ) -> List[Dict]:
        """
        Combine and rerank results from vector and graph searches.
        
        Uses a weighted scoring formula:
        S = α·Sim_vector + β·Sim_graph + γ·Recency
        """
        # For now, simple merge with vector results taking priority
        # In production, implement sophisticated re-ranking
        combined = []
        
        # Add vector results with their scores
        for result in vector_results[:30]:  # Top 30 from vector search
            combined.append({
                'type': 'vector',
                'score': result.get('score', 0),
                'data': result
            })
        
        # Add graph results
        for result in graph_results[:20]:  # Top 20 from graph
            combined.append({
                'type': 'graph',
                'score': 0.5,  # Default graph score
                'data': result
            })
        
        # Sort by score
        combined.sort(key=lambda x: x['score'], reverse=True)
        
        return combined
    
    async def _generate_context_brief(
        self,
        query: str,
        results: List[Dict],
        entities: List[str]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive context brief using Gemini.
        """
        # Format results for the LLM
        formatted_results = self._format_results_for_llm(results)
        
        brief_prompt = f"""
        User Query: {query}
        
        Extracted Entities: {', '.join(entities)}
        
        Retrieved Data:
        {formatted_results}
        
        Task: Create a comprehensive context brief that:
        1. Summarizes the most relevant information
        2. Identifies lateral connections (unrelated but useful insights)
        3. Flags any contradictions
        4. Provides relationship mappings
        5. Notes temporal context
        
        Return structured JSON with sections:
        - direct_matches
        - lateral_connections
        - relationship_map
        - contradictions
        - temporal_context
        - sources (with conversation IDs and timestamps)
        """
        
        response = await self.generate_response(
            prompt=brief_prompt,
            temperature="conservative",
            thinking_level="high",
            include_thoughts=True
        )
        
        # Parse the response
        try:
            import json
            context_brief = json.loads(response['response'])
        except:
            # Fallback if JSON parsing fails
            context_brief = {
                'raw_response': response['response'],
                'thought_process': response.get('thought'),
                'entities': entities,
                'result_count': len(results)
            }
        
        return context_brief
    
    def _format_results_for_llm(self, results: List[Dict]) -> str:
        """Format search results into readable text for LLM processing."""
        formatted = []
        
        for i, result in enumerate(results[:50], 1):  # Limit to top 50
            result_type = result.get('type', 'unknown')
            data = result.get('data', {})
            
            if result_type == 'vector':
                metadata = data.get('metadata', {})
                formatted.append(f"""
Result {i} [Vector Match - Score: {result.get('score', 0):.3f}]:
Source: {metadata.get('source', 'unknown')}
Timestamp: {metadata.get('timestamp', 'unknown')}
Content: {metadata.get('content', '')[:500]}...
""")
            elif result_type == 'graph':
                node = data.get('node', {})
                formatted.append(f"""
Result {i} [Graph Node - Depth: {data.get('depth', 0)}]:
Node: {node.get('name', 'unknown')}
Type: {node.get('type', 'unknown')}
Properties: {node.get('properties', {})}
""")
        
        return "\n".join(formatted)
