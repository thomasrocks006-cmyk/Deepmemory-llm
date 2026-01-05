"""
Coreference resolution system.
Resolves pronouns (he/she/they) to actual entity names.
"""

from typing import Dict, List, Any, Optional
from app.gemini_client import gemini_client
import json
import logging

logger = logging.getLogger(__name__)


class CoreferenceResolver:
    """
    Resolves pronouns to entity names in conversation text.
    Solves the "she said" → "Ella said" problem.
    """
    
    def __init__(self):
        self.entity_cache = {}  # Cache for conversation-level entity mappings
    
    async def resolve_conversation(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Resolve coreferences across an entire conversation.
        
        Args:
            messages: List of message dicts with 'content' field
            
        Returns:
            Messages with 'resolved_content' field added
        """
        logger.info(f"Resolving coreferences for {len(messages)} messages")
        
        # Step 1: Identify all entities in the conversation
        entities = await self._identify_entities(messages)
        
        # Step 2: Resolve pronouns for each message
        resolved_messages = []
        for msg in messages:
            resolved_content = await self._resolve_message(
                content=msg['content'],
                entities=entities,
                context=self._build_context(msg, messages)
            )
            
            msg_copy = msg.copy()
            msg_copy['resolved_content'] = resolved_content
            resolved_messages.append(msg_copy)
        
        logger.info("Coreference resolution complete")
        return resolved_messages
    
    async def _identify_entities(self, messages: List[Dict]) -> Dict[str, List[str]]:
        """
        Identify all named entities in the conversation.
        
        Returns:
            {
                'people': ['Ella', 'Jordy', ...],
                'projects': ['DeepMemory App', ...],
                'locations': ['Armadale', ...]
            }
        """
        # Combine all message content
        full_text = '\n'.join(msg['content'] for msg in messages)
        
        entity_prompt = f"""
        Analyze this conversation and extract all named entities.
        
        Conversation:
        {full_text[:5000]}  # Limit to first 5000 chars
        
        Return JSON with:
        {{
            "people": ["Name1", "Name2", ...],
            "projects": ["Project1", ...],
            "organizations": ["Org1", ...],
            "locations": ["Place1", ...]
        }}
        
        Only include entities explicitly mentioned (not inferred).
        """
        
        response = await gemini_client.generate_flash(
            prompt=entity_prompt,
            response_format="json"
        )
        
        try:
            entities = json.loads(response)
        except:
            entities = {"people": [], "projects": [], "organizations": [], "locations": []}
        
        return entities
    
    async def _resolve_message(
        self,
        content: str,
        entities: Dict[str, List[str]],
        context: str
    ) -> str:
        """
        Resolve pronouns in a single message.
        
        Args:
            content: Message content
            entities: Known entities from conversation
            context: Surrounding messages for context
            
        Returns:
            Content with pronouns resolved
        """
        # Check if message contains pronouns
        pronouns = ['he', 'she', 'they', 'him', 'her', 'them', 'his', 'hers', 'their']
        has_pronouns = any(pronoun in content.lower() for pronoun in pronouns)
        
        if not has_pronouns:
            return content  # No resolution needed
        
        resolution_prompt = f"""
        Resolve pronoun references in this message.
        
        Message: {content}
        
        Context (previous messages):
        {context}
        
        Known entities:
        People: {', '.join(entities.get('people', []))}
        Projects: {', '.join(entities.get('projects', []))}
        
        Return JSON with:
        {{
            "resolutions": [
                {{
                    "pronoun": "she",
                    "refers_to": "Ella",
                    "confidence": 0.95
                }}
            ],
            "resolved_text": "the message with pronouns replaced"
        }}
        
        If a pronoun is ambiguous, keep it as-is and mark confidence < 0.5.
        """
        
        response = await gemini_client.generate_flash(
            prompt=resolution_prompt,
            response_format="json"
        )
        
        try:
            result = json.loads(response)
            resolved = result.get('resolved_text', content)
            
            # Log resolutions with low confidence
            for res in result.get('resolutions', []):
                if res.get('confidence', 0) < 0.5:
                    logger.warning(f"Low confidence resolution: {res['pronoun']} → {res.get('refers_to', 'unknown')}")
            
            return resolved
        except:
            return content  # Return original if resolution fails
    
    def _build_context(
        self,
        current_message: Dict,
        all_messages: List[Dict],
        window_size: int = 3
    ) -> str:
        """
        Build context from surrounding messages.
        
        Args:
            current_message: The message being resolved
            all_messages: All messages in conversation
            window_size: Number of messages before/after to include
            
        Returns:
            Formatted context string
        """
        # Find current message index
        try:
            current_idx = all_messages.index(current_message)
        except ValueError:
            return ""
        
        # Get window
        start_idx = max(0, current_idx - window_size)
        end_idx = min(len(all_messages), current_idx + window_size + 1)
        
        context_messages = all_messages[start_idx:current_idx]
        
        # Format context
        context_parts = []
        for msg in context_messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:200]  # Limit length
            context_parts.append(f"{role.capitalize()}: {content}")
        
        return '\n'.join(context_parts)
    
    async def resolve_single_text(
        self,
        text: str,
        known_entities: Optional[List[str]] = None
    ) -> str:
        """
        Resolve coreferences in a single text snippet.
        Useful for real-time resolution during chat.
        
        Args:
            text: Text to resolve
            known_entities: List of entity names to consider
            
        Returns:
            Resolved text
        """
        if not known_entities:
            known_entities = []
        
        resolution_prompt = f"""
        Resolve pronoun references in this text.
        
        Text: {text}
        
        Known people: {', '.join(known_entities)}
        
        Return the text with pronouns resolved to specific names where possible.
        If ambiguous, keep the pronoun.
        """
        
        response = await gemini_client.generate_flash(prompt=resolution_prompt)
        
        return response.strip()
