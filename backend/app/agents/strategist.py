"""
Strategist Agent - User-facing advisor.
Synthesizes context into actionable advice.
"""

from typing import Dict, Any, List, Optional, AsyncIterator
from app.agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)


STRATEGIST_SYSTEM_PROMPT = """
You are Thomas's trusted Strategic Advisor with complete knowledge of his life, projects, and network.

You have access to:
1. The current conversation (Tier 1: Active memory)
2. A Context Brief from the Librarian (Tier 2-3: Historical memory)
3. Psychological profiles of key people in Thomas's network
4. Project status documents and technical specifications

Your communication style:
- Pedantic accuracy: Every claim must be traceable to source data
- Lateral thinking: Connect seemingly unrelated past experiences
- Psychological awareness: Consider how decisions affect key relationships
- Strategic foresight: Anticipate second and third-order consequences

When answering:
1. **Synthesize** the Librarian's findings (don't just repeat)
2. **Cite sources** in footnotes: [1: Conversation with Jordy, Jan 4, 2026]
3. **Consider personas**: How will Ella/Jordy/others perceive this?
4. **Flag conflicts**: If past statements contradict, highlight the evolution

Constraint: If the Librarian marked data as [INSUFFICIENT_DATA], acknowledge the gap.
"""


class StrategistAgent(BaseAgent):
    """
    The Strategist Agent is the user-facing advisor.
    It synthesizes context from the Librarian into actionable advice.
    """
    
    def __init__(self):
        super().__init__(
            name="Strategist",
            system_instruction=STRATEGIST_SYSTEM_PROMPT
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a strategic response based on context.
        
        Args:
            input_data: Dict with:
                - query: User's question
                - context_brief: From Librarian
                - personas: Relevant psychological profiles
                - conversation_history: Recent turns
                
        Returns:
            Strategic advice with sources
        """
        query = input_data.get("query", "")
        context_brief = input_data.get("context_brief", {})
        personas = input_data.get("personas", [])
        history = input_data.get("conversation_history", [])
        
        self.log_action("Generating strategic response", {"query_length": len(query)})
        
        # Build the comprehensive prompt
        full_prompt = self._build_prompt(
            query=query,
            context_brief=context_brief,
            personas=personas,
            history=history
        )
        
        # Generate response with high thinking
        response = await self.generate_response(
            prompt=full_prompt,
            temperature="balanced",
            thinking_level="high",
            include_thoughts=True
        )
        
        # Parse and structure the response
        structured_response = self._structure_response(
            response=response,
            sources=context_brief.get('sources', [])
        )
        
        self.log_action("Strategic response generated", {
            "response_length": len(structured_response.get('content', '')),
            "sources_cited": len(structured_response.get('sources', []))
        })
        
        return structured_response
    
    async def generate_streaming_response(
        self,
        input_data: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, str]]:
        """
        Generate streaming response for real-time display.
        
        Yields chunks with type ('thinking' or 'response') and content.
        """
        query = input_data.get("query", "")
        context_brief = input_data.get("context_brief", {})
        personas = input_data.get("personas", [])
        history = input_data.get("conversation_history", [])
        
        # Build prompt
        full_prompt = self._build_prompt(query, context_brief, personas, history)
        
        # Stream response
        async for chunk in self.generate_stream(full_prompt, temperature="balanced"):
            yield {
                'type': 'response',
                'content': chunk
            }
    
    def _build_prompt(
        self,
        query: str,
        context_brief: Dict[str, Any],
        personas: List[Dict],
        history: List[Dict]
    ) -> str:
        """Build the comprehensive prompt for the Strategist."""
        
        # Format conversation history
        history_text = self._format_history(history)
        
        # Format context brief
        context_text = self._format_context_brief(context_brief)
        
        # Format personas
        personas_text = self._format_personas(personas)
        
        prompt = f"""
=== CURRENT CONVERSATION ===
{history_text}

User: {query}

=== CONTEXT FROM LIBRARIAN ===
{context_text}

=== RELEVANT PERSONAS ===
{personas_text}

=== YOUR TASK ===
Provide strategic advice that:
1. Directly answers the user's question
2. Synthesizes insights from the context brief
3. Considers psychological profiles of relevant people
4. Anticipates consequences and implications
5. Cites sources for all factual claims

Format your response with:
- Clear, actionable advice
- Source citations as [N: Description]
- Any relevant warnings or considerations
"""
        
        return prompt
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history."""
        if not history:
            return "[No previous conversation history]"
        
        formatted = []
        for turn in history[-10:]:  # Last 10 turns
            role = turn.get('role', 'unknown')
            content = turn.get('content', '')
            formatted.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted)
    
    def _format_context_brief(self, context_brief: Dict[str, Any]) -> str:
        """Format the context brief from Librarian."""
        if not context_brief:
            return "[No context available]"
        
        sections = []
        
        # Direct matches
        if 'direct_matches' in context_brief:
            sections.append(f"Direct Matches:\n{context_brief['direct_matches']}")
        
        # Lateral connections
        if 'lateral_connections' in context_brief:
            sections.append(f"Lateral Connections:\n{context_brief['lateral_connections']}")
        
        # Relationship map
        if 'relationship_map' in context_brief:
            sections.append(f"Relationship Map:\n{context_brief['relationship_map']}")
        
        # Contradictions
        if 'contradictions' in context_brief:
            sections.append(f"Contradictions:\n{context_brief['contradictions']}")
        
        return "\n\n".join(sections) if sections else str(context_brief)
    
    def _format_personas(self, personas: List[Dict]) -> str:
        """Format psychological profiles."""
        if not personas:
            return "[No relevant personas]"
        
        formatted = []
        for persona in personas:
            name = persona.get('person_name', 'Unknown')
            profile = persona.get('profile', {})
            
            # Extract key insights
            primary_driver = profile.get('psychological_analysis', {}).get('primary_driver', {})
            
            formatted.append(f"""
{name}:
- Primary Motivation: {primary_driver.get('conclusion', 'N/A')}
- Confidence: {primary_driver.get('confidence', 0):.0%}
- Key Insight: {primary_driver.get('evidence_trace', [{}])[0].get('interpretation', 'N/A') if primary_driver.get('evidence_trace') else 'N/A'}
""")
        
        return "\n".join(formatted)
    
    def _structure_response(
        self,
        response: Dict[str, str],
        sources: List[Dict]
    ) -> Dict[str, Any]:
        """Structure the response with metadata."""
        
        return {
            'content': response.get('response', ''),
            'thinking': response.get('thought'),
            'sources': sources,
            'metadata': {
                'agent': 'Strategist',
                'thinking_level': 'high',
                'source_count': len(sources)
            }
        }
