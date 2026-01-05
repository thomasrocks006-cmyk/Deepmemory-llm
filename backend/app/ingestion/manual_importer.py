"""
Manual/Markdown conversation importer.
Parses plain text or markdown transcripts.
"""

import re
from typing import Iterator, Dict, Any, List
from app.ingestion.base_importer import ConversationImporter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ManualImporter(ConversationImporter):
    """Importer for manually pasted conversations or markdown files."""
    
    def __init__(self):
        super().__init__(source_type='manual')
    
    def parse(self, file_content: bytes) -> Iterator[Dict[str, Any]]:
        """
        Parse manual/markdown transcript.
        
        Expected formats:
        1. User: message\nAssistant: message
        2. Human: message\nAI: message
        3. Q: message\nA: message
        4. ## User\nmessage\n## Assistant\nmessage
        """
        try:
            text = file_content.decode('utf-8')
        except:
            text = str(file_content)
        
        messages = self._extract_messages(text)
        
        if messages:
            metadata = self.create_conversation_metadata(
                messages=messages,
                title="Manual Import"
            )
            
            yield {
                'conversation_id': f"manual-{hash(text[:100])}",
                'metadata': metadata,
                'messages': messages
            }
    
    def _extract_messages(self, text: str) -> List[Dict]:
        """Extract messages using various patterns."""
        messages = []
        
        # Try different patterns
        patterns = [
            # Pattern 1: "User: ...\nAssistant: ..."
            r'(?P<role>User|Assistant):\s*(?P<content>.*?)(?=\n(?:User|Assistant):|$)',
            # Pattern 2: "Human: ...\nAI: ..."
            r'(?P<role>Human|AI):\s*(?P<content>.*?)(?=\n(?:Human|AI):|$)',
            # Pattern 3: "Q: ...\nA: ..."
            r'(?P<role>Q|A):\s*(?P<content>.*?)(?=\n(?:Q|A):|$)',
            # Pattern 4: Markdown headers "## User"
            r'##?\s*(?P<role>User|Assistant|Human|AI)\s*\n(?P<content>.*?)(?=\n##|$)'
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.DOTALL | re.IGNORECASE))
            if matches:
                messages = self._process_matches(matches)
                break
        
        return messages
    
    def _process_matches(self, matches) -> List[Dict]:
        """Process regex matches into standardized messages."""
        messages = []
        
        for match in matches:
            role = match.group('role').strip()
            content = match.group('content').strip()
            
            if not content:
                continue
            
            # Map role variants
            role_map = {
                'user': 'user',
                'human': 'user',
                'q': 'user',
                'assistant': 'assistant',
                'ai': 'assistant',
                'a': 'assistant'
            }
            
            normalized_role = role_map.get(role.lower(), 'user')
            
            standardized = self.standardize_message(
                role=normalized_role,
                content=content,
                timestamp=datetime.now(),
                metadata={'source': 'manual_parse'}
            )
            
            messages.append(standardized)
        
        return messages
