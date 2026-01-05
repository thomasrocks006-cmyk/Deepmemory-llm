"""
Llama embeddings client using sentence-transformers.
Provides 1024-dimensional embeddings for Pinecone integration.
"""

from sentence_transformers import SentenceTransformer
from typing import List
import logging

logger = logging.getLogger(__name__)


class LlamaEmbeddingClient:
    """Client for generating Llama-based embeddings."""
    
    def __init__(self):
        """Initialize the Llama embedding model."""
        # Using a model that produces 1024-dimensional embeddings
        # This matches your Pinecone index configuration
        self.model = SentenceTransformer('BAAI/bge-large-en-v1.5')
        logger.info("Llama embedding model initialized (1024 dimensions)")
    
    def embed_text(
        self,
        text: str,
        task_type: str = "retrieval_document"
    ) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            task_type: Not used for Llama, kept for API compatibility
        
        Returns:
            1024-dimensional embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(
        self,
        texts: List[str],
        task_type: str = "retrieval_document"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            task_type: Not used for Llama, kept for API compatibility
        
        Returns:
            List of 1024-dimensional embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]
    
    async def create_specialized_embedding(
        self,
        text: str,
        dimension_type: str
    ) -> List[float]:
        """
        Create specialized embeddings for multi-vector search.
        
        Args:
            text: Original text
            dimension_type: 'semantic', 'sentiment', 'strategic', 'temporal'
        
        Returns:
            1024-dimensional embedding vector
        """
        # Create dimension-specific prompts
        prompts = {
            'semantic': text,
            'sentiment': f"Emotional tone and interpersonal dynamics: {text}",
            'strategic': f"Goals, decisions, and strategic implications: {text}",
            'temporal': f"Change or evolution in thinking: {text}"
        }
        
        prompt = prompts.get(dimension_type, text)
        return self.embed_text(prompt)


# Global instance
_llama_client = None


def get_llama_client() -> LlamaEmbeddingClient:
    """Get or create the global Llama embedding client."""
    global _llama_client
    if _llama_client is None:
        _llama_client = LlamaEmbeddingClient()
    return _llama_client
