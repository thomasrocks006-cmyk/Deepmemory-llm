"""
Pinecone vector database client for semantic search.
Handles multi-dimensional embeddings for lateral thinking retrieval.
"""

from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class PineconeClient:
    """Client for Pinecone vector database operations."""
    
    def __init__(self):
        """Initialize Pinecone client and index."""
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        
        # Create index if it doesn't exist
        self._ensure_index_exists()
        
        # Get index reference
        self.index = self.pc.Index(self.index_name)
    
    def _ensure_index_exists(self):
        """Create the index if it doesn't exist."""
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            logger.info(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=1024,  # Llama text-embed-v2 dimension (was 768 for Gemini)
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",  # Changed from gcp to match your Pinecone setup
                    region=settings.pinecone_environment
                )
            )
            logger.info(f"Index {self.index_name} created successfully")
    
    def upsert_embedding(
        self,
        vector_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        namespace: str = "semantic"
    ):
        """Upsert a single embedding with metadata."""
        self.index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                }
            ],
            namespace=namespace
        )
    
    def upsert_batch(
        self,
        vectors: List[Dict[str, Any]],
        namespace: str = "semantic",
        batch_size: int = 100
    ):
        """Upsert embeddings in batches for efficiency."""
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch, namespace=namespace)  # type: ignore
    
    def query(
        self,
        query_embedding: List[float],
        top_k: int = 50,
        namespace: str = "semantic",
        filter_dict: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> Dict:
        """Query the index for similar vectors."""
        result = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            filter=filter_dict,
            include_metadata=include_metadata
        )
        return dict(result)  # type: ignore
    
    def multi_dimensional_query(
        self,
        query_embeddings: Dict[str, List[float]],
        top_k: int = 50,
        weights: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Query across multiple embedding spaces and merge results.
        
        Args:
            query_embeddings: Dict with keys like 'semantic', 'sentiment', 'strategic'
            top_k: Number of results per dimension
            weights: Weights for each dimension (default: equal weight)
        """
        if weights is None:
            weights = {dim: 1.0 / len(query_embeddings) for dim in query_embeddings}
        
        # Query each namespace
        all_results = {}
        for dimension, embedding in query_embeddings.items():
            results = self.query(
                query_embedding=embedding,
                top_k=top_k,
                namespace=dimension
            )
            all_results[dimension] = results
        
        # Merge results using reciprocal rank fusion
        merged = self._reciprocal_rank_fusion(all_results, weights)
        
        return merged
    
    def _reciprocal_rank_fusion(
        self,
        results_by_dimension: Dict[str, Dict],
        weights: Dict[str, float],
        k: int = 60
    ) -> List[Dict]:
        """
        Merge results from multiple searches using Reciprocal Rank Fusion.
        RRF formula: score = sum(weight / (k + rank))
        """
        scores = {}
        metadata_cache = {}
        
        for dimension, results in results_by_dimension.items():
            weight = weights.get(dimension, 1.0)
            
            for rank, match in enumerate(results.get("matches", []), start=1):
                vector_id = match["id"]
                rrf_score = weight / (k + rank)
                
                if vector_id not in scores:
                    scores[vector_id] = 0
                    metadata_cache[vector_id] = match.get("metadata", {})
                
                scores[vector_id] += rrf_score
        
        # Sort by score descending
        sorted_results = sorted(
            [
                {
                    "id": vid,
                    "score": score,
                    "metadata": metadata_cache[vid]
                }
                for vid, score in scores.items()
            ],
            key=lambda x: x["score"],
            reverse=True
        )
        
        return sorted_results
    
    def delete_vectors(self, vector_ids: List[str], namespace: str = "semantic"):
        """Delete vectors by IDs."""
        self.index.delete(ids=vector_ids, namespace=namespace)
    
    def delete_all(self, namespace: str = "semantic"):
        """Delete all vectors in a namespace."""
        self.index.delete(delete_all=True, namespace=namespace)
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the index."""
        stats = self.index.describe_index_stats()
        return dict(stats)  # type: ignore


# Lazy initialization - only create when first accessed
_pinecone_client: Optional[PineconeClient] = None


def get_pinecone_client() -> PineconeClient:
    """Get or create the Pinecone client instance."""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = PineconeClient()
    return _pinecone_client


# For backward compatibility - but will fail if accessed before app startup
class LazyPineconeClient(PineconeClient):  # type: ignore
    """Lazy wrapper for backward compatibility with existing code."""
    _instance: Optional[PineconeClient] = None
    
    def __init__(self):
        # Don't call super().__init__() - lazy init
        pass
    
    def __getattr__(self, name):
        if self._instance is None:
            try:
                self._instance = get_pinecone_client()
            except Exception:
                # Return dummy methods if Pinecone fails
                return lambda *args, **kwargs: {} if name == 'get_index_stats' else None
        return getattr(self._instance, name)
    
    def get_index_stats(self) -> Dict:
        """Get index stats, with graceful fallback if not initialized."""
        try:
            if self._instance is None:
                self._instance = get_pinecone_client()
            return self._instance.get_index_stats()
        except Exception:
            return {'total_vector_count': 0, 'namespaces': {}}


pinecone_client = LazyPineconeClient()
