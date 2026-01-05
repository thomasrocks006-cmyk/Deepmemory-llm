"""
ChatGPT conversation importer.
Parses ChatGPT export JSON format.
"""

import json
from typing import Iterator, Dict, Any
from app.ingestion.base_importer import ConversationImporter
import logging

logger = logging.getLogger(__name__)


class ChatGPTImporter(ConversationImporter):
    """Importer for ChatGPT conversation exports."""
    
    def __init__(self):
        super().__init__(source_type='chatgpt')
    
    def parse(self, file_content: bytes) -> Iterator[Dict[str, Any]]:
        """
        Parse ChatGPT conversations.json file.
        
        ChatGPT export format:
        {
            "conversations": [
                {
                    "id": "conv-id",
                    "title": "Conversation title",
                    "create_time": timestamp,
                    "update_time": timestamp,
                    "mapping": {
                        "message-id": {
                            "id": "message-id",
                            "message": {
                                "author": {"role": "user|assistant"},
                                "content": {"parts": ["text"]},
                                "create_time": timestamp
                            }
                        }
                    }
                }
            ]
        }
        """
        try:
            data = json.loads(file_content.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to parse ChatGPT JSON: {e}")
            return
        
        conversations = data.get('conversations', [])
        
        for conv in conversations:
            try:
                parsed_conv = self._parse_conversation(conv)
                if parsed_conv:
                    yield parsed_conv
            except Exception as e:
                logger.error(f"Failed to parse conversation {conv.get('id')}: {e}")
    
    def _parse_conversation(self, conv: Dict) -> Dict[str, Any]:
        """Parse a single conversation."""
        messages = []
        mapping = conv.get('mapping', {})
        
        # Extract messages from mapping
        for message_id, message_data in mapping.items():
            message_obj = message_data.get('message')
            
            if not message_obj:
                continue
            
            author = message_obj.get('author', {})
            content = message_obj.get('content', {})
            
            role = author.get('role', 'user')
            parts = content.get('parts', [])
            
            # Skip empty messages
            if not parts or not any(parts):
                continue
            
            # Combine all parts
            text = '\n'.join(str(part) for part in parts if part)
            
            timestamp = message_obj.get('create_time')
            
            standardized = self.standardize_message(
                role=role,
                content=text,
                timestamp=timestamp,
                metadata={
                    'message_id': message_id,
                    'conversation_id': conv.get('id')
                }
            )
            
            messages.append(standardized)
        
        if not messages:
            return {}  # Return empty dict instead of None
        
        # Sort by timestamp
        messages.sort(key=lambda x: x['timestamp'])
        
        # Create conversation metadata
        metadata = self.create_conversation_metadata(
            messages=messages,
            title=conv.get('title', 'Untitled ChatGPT Conversation')
        )
        
        return {
            'conversation_id': conv.get('id'),
            'metadata': metadata,
            'messages': messages
        }
