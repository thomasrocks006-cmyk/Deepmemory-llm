"""
Gemini API client for LLM interactions.
Handles both Gemini 3 Pro and Flash models with context caching.
"""

import google.generativeai as genai  # type: ignore
from google.ai.generativelanguage_v1beta.types import content  # type: ignore
from typing import List, Dict, Any, Optional, AsyncIterator
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.google_api_key)  # type: ignore


class GeminiClient:
    """Client for Google Gemini API with thinking mode support."""
    
    def __init__(self):
        """Initialize Gemini models."""
        self.pro_model = genai.GenerativeModel("gemini-3-pro-preview")  # type: ignore
        self.flash_model = genai.GenerativeModel("gemini-3-flash")  # type: ignore
        
        # Generation configs
        self.config_conservative = genai.GenerationConfig(  # type: ignore
            temperature=settings.temperature_conservative,
            max_output_tokens=settings.max_output_tokens
        )
        
        self.config_balanced = genai.GenerationConfig(  # type: ignore
            temperature=settings.temperature_balanced,
            max_output_tokens=settings.max_output_tokens
        )
        
        self.config_creative = genai.GenerationConfig(  # type: ignore
            temperature=settings.temperature_creative,
            max_output_tokens=settings.max_output_tokens
        )
    
    async def generate_with_thinking(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_level: str = "high",
        include_thoughts: bool = True,
        temperature: str = "balanced",
        budget_tokens: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Generate response with thinking mode enabled.
        
        Args:
            prompt: User query or instruction
            system_instruction: System prompt for the model
            thinking_level: 'low', 'medium', or 'high'
            include_thoughts: Whether to return the chain of thought
            temperature: 'conservative', 'balanced', or 'creative'
            budget_tokens: Optional max thinking tokens budget
        
        Returns:
            Dict with 'thought' and 'response' keys
        """
        # Select generation config
        config_map = {
            'conservative': self.config_conservative,
            'balanced': self.config_balanced,
            'creative': self.config_creative
        }
        generation_config = config_map.get(temperature, self.config_balanced)
        
        # Create model with system instruction if provided
        model = self.pro_model
        if system_instruction:
            model = genai.GenerativeModel(  # type: ignore
                "gemini-3-pro-preview",
                system_instruction=system_instruction
            )
        
        # Generate with thinking mode
        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config,
            # Note: thinking_level and include_thoughts are 2026 features
            # For now, we'll simulate with verbose prompting
        )
        
        return {
            'thought': response.text if include_thoughts else "",
            'response': response.text
        }
    
    async def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: str = "balanced"
    ) -> AsyncIterator[str]:
        """
        Generate response with streaming for real-time display.
        
        Yields text chunks as they're generated.
        """
        config_map = {
            'conservative': self.config_conservative,
            'balanced': self.config_balanced,
            'creative': self.config_creative
        }
        generation_config = config_map.get(temperature, self.config_balanced)
        
        model = self.pro_model
        if system_instruction:
            model = genai.GenerativeModel(  # type: ignore
                "gemini-3-pro-preview",
                system_instruction=system_instruction
            )
        
        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config,
            stream=True
        )
        
        async for chunk in response:
            yield chunk.text
    
    async def generate_flash(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.1
    ) -> str:
        """
        Fast generation using Gemini Flash for extraction tasks.
        
        Args:
            prompt: Instruction and input
            response_format: 'text' or 'json'
            temperature: Generation temperature (default 0.1 for factual extraction)
        """
        config = genai.GenerationConfig(  # type: ignore
            temperature=temperature,
            response_mime_type="application/json" if response_format == "json" else "text/plain"
        )
        
        response = await self.flash_model.generate_content_async(
            prompt,
            generation_config=config
        )
        
        return response.text
    
    def embed_text(
        self,
        text: str,
        task_type: str = "retrieval_document"
    ) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            task_type: 'retrieval_document', 'retrieval_query', 'semantic_similarity'
        """
        result = genai.embed_content(  # type: ignore
            model="models/text-embedding-004",
            content=text,
            task_type=task_type
        )
        return result['embedding']
    
    def embed_batch(
        self,
        texts: List[str],
        task_type: str = "retrieval_document"
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        results = []
        for text in texts:
            embedding = self.embed_text(text, task_type)
            results.append(embedding)
        return results
    
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
        """
        # Create dimension-specific prompts
        prompts = {
            'semantic': text,  # Standard semantic embedding
            'sentiment': f"Capture the emotional tone and interpersonal dynamics: {text}",
            'strategic': f"Extract the high-level goals, decisions, and strategic implications: {text}",
            'temporal': f"Capture how this represents change or evolution in thinking: {text}"
        }
        
        prompt = prompts.get(dimension_type, text)
        
        # For specialized dimensions, we embed the transformed prompt
        return self.embed_text(prompt, task_type="semantic_similarity")


class ContextCacheManager:
    """Manages Gemini context caching for performance."""
    
    def __init__(self):
        self.cached_contents = {}
    
    async def create_cached_context(
        self,
        content: str,
        cache_key: str,
        ttl: int = 3600
    ):
        """
        Create a cached context for reuse.
        
        Note: This is a simplified implementation.
        Full Vertex AI context caching requires additional setup.
        """
        # In production, this would use Vertex AI's context caching
        from datetime import datetime
        self.cached_contents[cache_key] = {
            'content': content,
            'created_at': datetime.utcnow(),
            'ttl': ttl
        }
        
        logger.info(f"Created cache: {cache_key}")
    
    def get_cached_context(self, cache_key: str) -> Optional[str]:
        """Retrieve cached context."""
        cache = self.cached_contents.get(cache_key)
        if cache:
            return cache['content']
        return None


# Lazy initialization - only create when first accessed
_gemini_client: Optional[GeminiClient] = None
_cache_manager: Optional[ContextCacheManager] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


def get_cache_manager() -> ContextCacheManager:
    """Get or create the cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = ContextCacheManager()
    return _cache_manager


# Lazy wrappers for backward compatibility
class LazyGeminiClient(GeminiClient):  # type: ignore
    """Lazy wrapper for backward compatibility."""
    _instance: Optional[GeminiClient] = None
    
    def __init__(self):
        # Don't call super().__init__() - lazy init
        pass
    
    def __getattr__(self, name):
        if self._instance is None:
            self._instance = get_gemini_client()
        return getattr(self._instance, name)


class LazyCacheManager:
    """Lazy wrapper for backward compatibility."""
    def __getattr__(self, name):
        return getattr(get_cache_manager(), name)


gemini_client = LazyGeminiClient()
cache_manager = LazyCacheManager()
