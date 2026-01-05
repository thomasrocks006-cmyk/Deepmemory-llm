"""
Gemini conversation importer.
Parses Gemini/Google Takeout export format.
"""

import json
from typing import Iterator, Dict, Any, List
from app.ingestion.base_importer import ConversationImporter
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class GeminiImporter(ConversationImporter):
    """Importer for Gemini conversation exports from Google Takeout."""
    
    def __init__(self):
        super().__init__(source_type='gemini')
    
    def parse(self, file_content: bytes) -> Iterator[Dict[str, Any]]:
        """
        Parse Gemini conversation data.
        
        Google Takeout can export as:
        1. HTML files (activity records)
        2. JSON files (conversation data)
        
        We'll handle both formats.
        """
        try:
            # Try JSON first
            data = json.loads(file_content.decode('utf-8'))
            yield from self._parse_json_format(data)
        except json.JSONDecodeError:
            # Try HTML format
            try:
                yield from self._parse_html_format(file_content)
            except Exception as e:
                logger.error(f"Failed to parse Gemini data: {e}")
    
    def _parse_json_format(self, data: Dict) -> Iterator[Dict[str, Any]]:
        """Parse JSON format export."""
        # Gemini JSON structure varies, handle common patterns
        
        if 'conversations' in data:
            # Structured format
            for conv in data['conversations']:
                yield self._parse_conversation_json(conv)
        elif 'messages' in data:
            # Flat messages format
            messages = self._parse_messages_json(data['messages'])
            if messages:
                metadata = self.create_conversation_metadata(messages)
                yield {
                    'conversation_id': data.get('id', 'gemini-import'),
                    'metadata': metadata,
                    'messages': messages
                }
    
    def _parse_html_format(self, file_content: bytes) -> Iterator[Dict[str, Any]]:
        """Parse HTML activity export."""
        soup = BeautifulSoup(file_content, 'html.parser')
        
        # Find conversation blocks
        # This is a heuristic approach - adjust based on actual HTML structure
        conversation_blocks = soup.find_all('div', class_=['conversation', 'chat'])
        
        for block in conversation_blocks:
            messages = self._extract_messages_from_html(block)
            if messages:
                metadata = self.create_conversation_metadata(messages)
                yield {
                    'conversation_id': f"gemini-html-{hash(str(block))}",
                    'metadata': metadata,
                    'messages': messages
                }
    
    def _parse_conversation_json(self, conv: Dict) -> Dict[str, Any]:
        """Parse a single conversation from JSON."""
        messages = []
        
        for msg in conv.get('messages', []):
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp')
            
            standardized = self.standardize_message(
                role=role,
                content=content,
                timestamp=timestamp,
                metadata={
                    'message_id': msg.get('id'),
                    'conversation_id': conv.get('id')
                }
            )
            
            messages.append(standardized)
        
        metadata = self.create_conversation_metadata(
            messages=messages,
            title=conv.get('title', 'Gemini Conversation')
        )
        
        return {
            'conversation_id': conv.get('id'),
            'metadata': metadata,
            'messages': messages
        }
    
    def _parse_messages_json(self, messages_data: List[Dict]) -> List[Dict]:
        """Parse flat messages array."""
        messages = []
        
        for msg in messages_data:
            role = msg.get('author', 'user')
            content = msg.get('text', msg.get('content', ''))
            timestamp = msg.get('time', msg.get('timestamp'))
            
            standardized = self.standardize_message(
                role=role,
                content=content,
                timestamp=timestamp,
                metadata=msg
            )
            
            messages.append(standardized)
        
        return messages
    
    def _extract_messages_from_html(self, block) -> List[Dict]:
        """Extract messages from HTML block."""
        messages = []
        
        # Find message elements
        message_elements = block.find_all(['p', 'div'], class_=['message', 'text'])
        
        for elem in message_elements:
            # Determine role (heuristic)
            parent = elem.find_parent(['div', 'section'])
            role = 'user' if 'user' in str(parent.get('class', [])) else 'assistant'
            
            content = elem.get_text(strip=True)
            
            if content:
                standardized = self.standardize_message(
                    role=role,
                    content=content,
                    timestamp=None,
                    metadata={'source_html': True}
                )
                messages.append(standardized)
        
        return messages
