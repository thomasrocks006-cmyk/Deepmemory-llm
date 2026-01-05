"""
Learning Loop Module
Implements continuous improvement through post-turn extraction, conflict detection,
and background reflection.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import (
    Conversation, Message, Persona, Scratchpad, 
    Conflict, Insight, Summary
)
from app.gemini_client import GeminiClient
from app.llama_embeddings import get_llama_client
from app.vector_db import PineconeClient
from app.graph_db import Neo4jClient
from app.database import get_db


class LearningLoop:
    """
    Continuous learning system that extracts knowledge after each interaction
    """
    
    def __init__(
        self,
        gemini_client: GeminiClient,
        vector_db: PineconeClient,
        graph_db: Neo4jClient,
    ):
        self.gemini = gemini_client
        self.vector_db = vector_db
        self.graph_db = graph_db
        
    async def post_turn_extraction(
        self,
        conversation_id: str,
        message_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Extract insights after each assistant turn
        
        Returns:
            - facts: New factual information
            - entities: Mentioned people, places, concepts
            - sentiment: Emotional tone
            - conflicts: Detected contradictions
        """
        message = db.query(Message).filter_by(id=message_id).first()
        if not message:
            return {}
            
        # Get recent context
        recent_messages = db.query(Message).filter_by(
            conversation_id=conversation_id
        ).order_by(desc(Message.created_at)).limit(10).all()
        
        context = "\n".join([
            f"{m.role}: {m.content}"
            for m in reversed(recent_messages)
        ])
        
        # Extract facts and entities
        extraction_prompt = f"""Analyze this conversation turn and extract:

CONVERSATION:
{context}

EXTRACT:
1. **New Facts**: Concrete information about the user (preferences, experiences, goals)
2. **Entities**: People, places, concepts mentioned
3. **Emotional State**: Current mood and sentiment
4. **Value Signals**: What matters to the user

Return as JSON:
{{
    "facts": ["fact1", "fact2"],
    "entities": [{{"name": "entity", "type": "person/place/concept", "context": "..."}}],
    "sentiment": {{"valence": 0-100, "arousal": 0-100, "dominance": 0-100}},
    "values": ["value1", "value2"]
}}"""
        
        extraction = await self.gemini.generate_flash(extraction_prompt, response_format="json", temperature=0.3)
        
        try:
            import json
            extracted = json.loads(extraction)
        except:
            extracted = {
                "facts": [],
                "entities": [],
                "sentiment": {},
                "values": []
            }
        
        # Store entities in knowledge graph
        if extracted.get("entities"):
            await self._update_knowledge_graph(extracted["entities"], message_id, db)
        
        # Detect conflicts with existing knowledge
        conflicts = await self._detect_conflicts(extracted.get("facts", []), db)
        
        # Update scratchpad
        await self._update_scratchpad(conversation_id, extracted, db)
        
        return {
            "extracted": extracted,
            "conflicts": conflicts,
            "entities_added": len(extracted.get("entities", []))
        }
    
    async def _update_knowledge_graph(
        self,
        entities: List[Dict[str, str]],
        message_id: str,
        db: Session
    ):
        """Add entities and relationships to Neo4j graph"""
        for entity in entities:
            # Create or update entity node using existing method
            self.graph_db.create_or_update_node(
                label=entity["type"].capitalize(),
                name=entity["name"],
                properties={"context": entity.get("context", "")}
            )
            
            # Create a Message node for linking
            self.graph_db.create_or_update_node(
                label="Message",
                name=message_id,
                properties={"type": "message"}
            )
            
            # Link entity to message
            self.graph_db.create_relationship(
                from_label=entity["type"].capitalize(),
                from_name=entity["name"],
                to_label="Message",
                to_name=message_id,
                relationship_type="MENTIONED_IN",
                properties={"timestamp": datetime.utcnow().isoformat()}
            )
    
    async def _detect_conflicts(
        self,
        new_facts: List[str],
        db: Session
    ) -> List[Dict[str, Any]]:
        """Detect contradictions with existing knowledge"""
        conflicts_found = []
        
        # Get Llama embedding client
        llama_client = get_llama_client()
        
        for fact in new_facts:
            # Embed the new fact using Llama embeddings
            fact_embedding = llama_client.embed_text(fact)
            
            # Search for similar statements using query method
            similar = self.vector_db.query(
                query_embedding=fact_embedding,
                top_k=5,
                filter_dict={"type": "fact"}
            )
            
            if not similar:
                continue
            
            # Check for contradictions using LLM
            for match in similar:
                if match["score"] > 0.85:  # High similarity
                    conflict_check_prompt = f"""Compare these two statements:

STATEMENT 1: {fact}
STATEMENT 2: {match['metadata'].get('content', '')}

Do they contradict each other? Answer with JSON:
{{
    "is_conflict": true/false,
    "explanation": "why they conflict or don't",
    "severity": "minor/moderate/major"
}}"""
                    
                    result = await self.gemini.generate_flash(
                        conflict_check_prompt, 
                        temperature=0.2
                    )
                    
                    try:
                        import json
                        conflict_data = json.loads(result)
                        
                        if conflict_data.get("is_conflict"):
                            # Store conflict
                            conflict = Conflict(
                                statement_a=fact,
                                statement_b=match['metadata'].get('content', ''),
                                explanation=conflict_data.get("explanation", ""),
                                severity=conflict_data.get("severity", "moderate"),
                                resolved=False
                            )
                            db.add(conflict)
                            conflicts_found.append({
                                "fact": fact,
                                "conflicts_with": match['metadata'].get('content', ''),
                                "explanation": conflict_data.get("explanation", ""),
                                "severity": conflict_data.get("severity", "moderate")
                            })
                    except:
                        pass
        
        db.commit()
        return conflicts_found
    
    async def _update_scratchpad(
        self,
        conversation_id: str,
        extracted: Dict[str, Any],
        db: Session
    ):
        """Update the living document scratchpad"""
        # Get or create scratchpad
        scratchpad = db.query(Scratchpad).filter_by(
            conversation_id=conversation_id
        ).first()
        
        if not scratchpad:
            scratchpad = Scratchpad(
                conversation_id=conversation_id,
                content="# Conversation Notes\n\n"
            )
            db.add(scratchpad)
        
        # Generate update using LLM
        update_prompt = f"""Update this living document with new information:

CURRENT NOTES:
{scratchpad.content}

NEW INFORMATION:
- Facts: {extracted.get('facts', [])}
- Values: {extracted.get('values', [])}
- Sentiment: {extracted.get('sentiment', {})}

Update the notes to incorporate this information. Keep it concise and organized.
Return only the updated document."""
        
        updated_content = await self.gemini.generate_flash(update_prompt, response_format="text")
        # Use object attribute assignment with refresh
        scratchpad_obj = db.query(Scratchpad).filter_by(id=scratchpad.id).first()
        if scratchpad_obj:
            scratchpad_obj.content = updated_content  # type: ignore
            scratchpad_obj.last_updated = datetime.utcnow()  # type: ignore
        db.commit()
    
    async def reflection_event(
        self,
        conversation_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Periodic reflection to generate meta-insights
        Triggered every 5 turns
        """
        # Get all messages in conversation
        messages = db.query(Message).filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at).all()
        
        # Get conversation metadata
        conversation = db.query(Conversation).filter_by(id=conversation_id).first()
        
        # Generate reflection
        reflection_prompt = f"""Reflect on this conversation and generate meta-insights:

CONVERSATION ({len(messages)} messages):
{self._format_messages_for_reflection(messages)}

GENERATE:
1. **Patterns**: What themes or patterns emerge?
2. **Growth**: How has the user's thinking evolved?
3. **Opportunities**: What could be explored deeper?
4. **Blind Spots**: What might the user be missing?

Return as JSON:
{{
    "patterns": ["pattern1", "pattern2"],
    "growth": "description of evolution",
    "opportunities": ["topic1", "topic2"],
    "blind_spots": ["blindspot1"]
}}"""
        
        response = await self.gemini.generate_with_thinking(
            prompt=reflection_prompt,
            temperature="balanced",
            budget_tokens=4096
        )
        reflection = response.get('response', '')
        
        try:
            import json
            insight_data = json.loads(reflection)
            
            # Store as insight
            insight = Insight(
                conversation_id=conversation_id,
                insight_type="reflection",
                content=reflection,
                metadata=insight_data
            )
            db.add(insight)
            db.commit()
            
            return insight_data
        except:
            return {}
    
    def _format_messages_for_reflection(self, messages: List[Message]) -> str:
        """Format messages for reflection prompt"""
        formatted = []
        for msg in messages[-20:]:  # Last 20 messages
            formatted.append(f"{msg.role.upper()}: {msg.content[:200]}...")
        return "\n".join(formatted)
    
    async def subconscious_agent(
        self,
        db: Session,
        lookback_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Nightly background processing to generate insights
        Runs async to find deep patterns
        """
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Get recent conversations
        conversations = db.query(Conversation).filter(
            Conversation.created_at >= cutoff_date
        ).all()
        
        insights = []
        
        for conv in conversations:
            # Get all messages
            messages = db.query(Message).filter_by(
                conversation_id=conv.id
            ).order_by(Message.created_at).all()
            
            if len(messages) < 5:  # Skip short conversations
                continue
            
            # Generate deep insight
            insight_prompt = f"""Deep analysis of conversation patterns:

CONVERSATION: {conv.id}
MESSAGES: {len(messages)}
TIMESPAN: {(messages[-1].created_at - messages[0].created_at).days} days

ANALYZE:
1. Hidden motivations behind questions
2. Unconscious patterns in topics
3. Emotional undertones
4. Future needs prediction

Return JSON:
{{
    "hidden_motivations": ["motivation1"],
    "patterns": ["pattern1"],
    "emotional_themes": ["theme1"],
    "predicted_needs": ["need1"]
}}"""
            
            response = await self.gemini.generate_with_thinking(
                prompt=insight_prompt,
                temperature="balanced",
                budget_tokens=4096
            )
            result = response.get('response', '')
            
            try:
                import json
                insight_data = json.loads(result)
                
                insight = Insight(
                    conversation_id=conv.id,
                    insight_type="subconscious",
                    content=result,
                    metadata=insight_data
                )
                db.add(insight)
                insights.append(insight_data)
            except:
                pass
        
        db.commit()
        return insights
    
    async def summarize_tier(
        self,
        conversation_id: str,
        tier: int,
        db: Session
    ) -> str:
        """
        Hierarchical summarization for memory compression
        Tier 1 → Tier 2 → Tier 3
        """
        # Get messages to summarize
        messages = db.query(Message).filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at).all()
        
        # Check if summary already exists
        existing_summary = db.query(Summary).filter_by(
            conversation_id=conversation_id,
            tier=tier
        ).first()
        
        if tier == 1:
            # Summarize recent 100k tokens
            content = "\n".join([
                f"{m.role}: {m.content}"
                for m in messages[-50:]  # Approximate
            ])
        elif tier == 2:
            # Summarize from tier 1 summaries
            tier1_summaries = db.query(Summary).filter_by(
                conversation_id=conversation_id,
                tier=1
            ).all()
            content = "\n".join([str(s.content) for s in tier1_summaries])
        else:
            # Tier 3 - ultra compressed
            tier2_summaries = db.query(Summary).filter_by(
                conversation_id=conversation_id,
                tier=2
            ).all()
            content = "\n".join([str(s.content) for s in tier2_summaries])
        
        summary_prompt = f"""Create a {tier}-tier summary of this conversation:

CONTENT:
{content[:10000]}  # Limit for context

TIER {tier} SUMMARY REQUIREMENTS:
- Tier 1: Detailed, preserve nuance
- Tier 2: Condensed, key points only
- Tier 3: Ultra-compressed, main themes

Return concise summary:"""
        
        summary_text = await self.gemini.generate_flash(
            summary_prompt,
            temperature=0.3
        )
        
        if existing_summary:
            # Use object attribute assignment with type ignore
            existing_summary.content = summary_text  # type: ignore
            existing_summary.updated_at = datetime.utcnow()  # type: ignore
        else:
            summary = Summary(
                conversation_id=conversation_id,
                tier=tier,
                content=summary_text
            )
            db.add(summary)
        
        db.commit()
        return summary_text
