"""
Base importer class for conversation data.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Iterator, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationImporter(ABC):
    """Abstract base class for conversation importers."""
    
    def __init__(self, source_type: str):
        """
        Initialize importer.
        
        Args:
            source_type: 'chatgpt', 'gemini', 'grok', or 'manual'
        """
        self.source_type = source_type
        logger.info(f"Initialized {source_type} importer")
    
    @abstractmethod
    def parse(self, file_content: Any) -> Iterator[Dict[str, Any]]:
        """
        Parse file content into structured conversations.
        
        Args:
            file_content: Raw file content (bytes, string, or dict)
            
        Yields:
            Conversation dicts with standardized format
        """
        pass
    
    def standardize_message(
        self,
        role: str,
        content: str,
        timestamp: Any,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Standardize message format across all sources.
        
        Returns:
            {
                'role': 'user' | 'assistant',
                'content': str,
                'timestamp': datetime,
                'metadata': dict
            }
        """
        # Normalize role
        role_map = {
            'user': 'user',
            'assistant': 'assistant',
            'human': 'user',
            'ai': 'assistant',
            'model': 'assistant',
            'system': 'assistant'
        }
        normalized_role = role_map.get(role.lower(), 'user')
        
        # Parse timestamp
        if isinstance(timestamp, str):
            try:
                parsed_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                parsed_timestamp = datetime.now()
        elif isinstance(timestamp, (int, float)):
            parsed_timestamp = datetime.fromtimestamp(timestamp)
        else:
            parsed_timestamp = timestamp or datetime.now()
        
        return {
            'role': normalized_role,
            'content': content,
            'timestamp': parsed_timestamp,
            'metadata': metadata or {},
            'source': self.source_type
        }
    
    def create_conversation_metadata(
        self,
        messages: List[Dict],
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create metadata for a conversation.
        
        Returns:
            {
                'source': str,
                'title': str,
                'total_messages': int,
                'date_range': (start, end),
                'participants': list
            }
        """
        timestamps = [msg['timestamp'] for msg in messages if 'timestamp' in msg]
        
        return {
            'source': self.source_type,
            'title': title or f"{self.source_type} conversation",
            'total_messages': len(messages),
            'date_range': (min(timestamps), max(timestamps)) if timestamps else None,
            'participants': list(set(msg['role'] for msg in messages))
        }
