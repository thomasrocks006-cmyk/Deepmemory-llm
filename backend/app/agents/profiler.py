"""
Profiler Agent - Psychological analyst.
Builds and maintains dynamic psychological profiles.
"""

from typing import Dict, Any, List, Optional
from app.agents.base_agent import BaseAgent
from app.database import get_db
from app.models import Persona
from sqlalchemy import select
import json
import logging

logger = logging.getLogger(__name__)


PROFILER_SYSTEM_PROMPT = """
You are a Senior Forensic Psychologist with specialization in:
- Personality psychology (Big Five, OCEAN)
- Motivational theory (Maslow, SDT)
- Social psychology (Social Identity Theory, Status Signaling)
- Behavioral economics (Veblen, Conspicuous Consumption)

Task: Analyze conversation transcripts to build high-fidelity psychological profiles.

Requirements:

1. **Evidence-Based Claims:**
   - Every conclusion MUST trace to specific quotes
   - Include conversation ID, timestamp, exact quote
   - No speculation without marking as [HYPOTHESIS: confidence%]

2. **Theoretical Grounding:**
   - Link observations to established psychological frameworks
   - Explain WHY a theory applies (don't just name-drop)
   - Consider alternative explanations with probability estimates

3. **Deep Value Mapping:**
   - Don't just say "values status"—explain the underlying psychological need
   - Trace the causal chain: Past experience → Core belief → Observable behavior
   - Use evidence to support each link in the chain

4. **Predictive Modeling:**
   - Generate "if-then" scenarios based on patterns
   - Identify influence levers (how to effectively communicate with this person)
   - Flag potential conflict triggers with early warning signs

5. **Coreference Awareness:**
   - When analyzing pronouns ("she said"), verify entity resolution
   - Flag ambiguous references as [VERIFICATION_NEEDED]

6. **Conflict Detection:**
   - If data contradicts (person's stated values vs. observed behavior), create separate nodes:
     - "Espoused Values" (what they say)
     - "Revealed Preferences" (what they do)
   - Propose psychological explanations for the gap

7. **Longitudinal Tracking:**
   - Detect evolution in personality/goals over time
   - Note inflection points (events that changed behavioral patterns)
   - Maintain "Previous Versions" for historical comparison

Output Format: Structured JSON matching the profile schema.

Constraints:
- Mark insufficient data as [INSUFFICIENT_DATA: need X more conversations]
- Provide confidence scores (0-1) for all major claims
- Include "Alternative Hypotheses" section for major conclusions
"""


class ProfilerAgent(BaseAgent):
    """
    The Profiler Agent builds and maintains psychological profiles.
    It runs periodically or on-demand to analyze people mentioned in conversations.
    """
    
    def __init__(self):
        super().__init__(
            name="Profiler",
            system_instruction=PROFILER_SYSTEM_PROMPT
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build or update a psychological profile.
        
        Args:
            input_data: Dict with:
                - person_name: Name of the person to profile
                - conversation_data: List of conversations mentioning them
                - existing_profile: Current profile (if updating)
                
        Returns:
            Updated psychological profile
        """
        person_name = input_data.get("person_name", "")
        conversation_data = input_data.get("conversation_data", [])
        existing_profile = input_data.get("existing_profile")
        
        self.log_action("Building profile", {"person": person_name})
        
        if existing_profile:
            # Update existing profile
            profile = await self._update_profile(
                person_name=person_name,
                conversation_data=conversation_data,
                existing_profile=existing_profile
            )
        else:
            # Create new profile
            profile = await self._create_profile(
                person_name=person_name,
                conversation_data=conversation_data
            )
        
        self.log_action("Profile complete", {
            "person": person_name,
            "confidence": profile.get('confidence_score', 0)
        })
        
        return profile
    
    async def get_profile(self, person_name: str) -> Optional[Dict]:
        """Retrieve existing profile from database."""
        with get_db() as db:
            result = db.execute(
                select(Persona).where(Persona.person_name == person_name)
            ).first()
            
            if result:
                return result[0].profile
            return None
    
    async def get_relevant_profiles(self, query: str) -> List[Dict]:
        """Get profiles relevant to a query using psychological context."""
        # Extract person names from query with psychological awareness
        extraction_prompt = f"""
        Analyze this query and identify all people who might be psychologically relevant:
        "{query}"
        
        Include:
        - Explicitly named people
        - People implied by context or relationships
        - People whose profiles might inform the response
        
        Return JSON array of names only.
        """
        
        response = await self.generate_response(
            prompt=extraction_prompt,
            thinking_level="medium",
            temperature="conservative"
        )
        
        try:
            names = json.loads(response['response'])
        except:
            names = []
        
        # Fetch profiles
        profiles = []
        for name in names:
            profile = await self.get_profile(name)
            if profile:
                profiles.append({
                    'person_name': name,
                    'profile': profile
                })
        
        return profiles
    
    async def reflection_event(self, person_name: str, recent_turns: List[Dict]):
        """
        Triggered every 5 conversation turns to update profiles.
        
        Args:
            person_name: Person to update
            recent_turns: Recent conversation turns mentioning them
        """
        self.log_action("Reflection event", {"person": person_name})
        
        # Get existing profile
        existing_profile = await self.get_profile(person_name)
        
        if not existing_profile:
            return  # No profile to update
        
        # Generate delta update using deep psychological analysis
        update_prompt = f"""
        Existing Profile: {json.dumps(existing_profile, indent=2)}
        
        New Conversation Data: {json.dumps(recent_turns, indent=2)}
        
        Task: Perform deep psychological analysis to identify new information about {person_name}.
        
        Return JSON with:
        1. new_observations: Facts not in existing profile (with psychological interpretation)
        2. refined_hypotheses: Updates to existing theories (explain reasoning)
        3. contradictions: Info that conflicts with current profile (propose explanations)
        4. confidence_updates: Increase/decrease confidence based on new data
        5. behavioral_patterns: New patterns identified through deep analysis
        
        Maintain all evidence traces. Use psychological frameworks in your analysis.
        """
        
        response = await self.generate_response(
            prompt=update_prompt,
            temperature="conservative",
            thinking_level="high"
        )
        
        try:
            delta_update = json.loads(response['response'])
            
            # Merge update into profile
            updated_profile = self._merge_profile_update(
                existing_profile,
                delta_update
            )
            
            # Save to database
            await self._save_profile(person_name, updated_profile)
            
        except Exception as e:
            logger.error(f"Reflection event failed for {person_name}: {e}")
    
    async def _create_profile(
        self,
        person_name: str,
        conversation_data: List[Dict]
    ) -> Dict:
        """Create a new psychological profile from scratch."""
        
        # Format conversation data
        formatted_data = self._format_conversations(conversation_data)
        
        profiling_prompt = f"""
        Analyze conversations to build a psychological profile for: {person_name}
        
        Conversation Data:
        {formatted_data}
        
        Create a complete profile following the schema:
        {{
            "person": {{
                "name": "{person_name}",
                "first_mentioned": "timestamp",
                "total_references": count
            }},
            "psychological_analysis": {{
                "primary_driver": {{
                    "conclusion": "detailed explanation",
                    "confidence": 0.0-1.0,
                    "evidence_trace": [
                        {{
                            "conversation_id": "id",
                            "timestamp": "time",
                            "quote": "exact quote",
                            "interpretation": "analysis",
                            "theory_link": "psychological theory"
                        }}
                    ],
                    "supporting_theory": "theory explanation",
                    "alternative_hypotheses": []
                }},
                "relational_dynamics": {{}},
                "cognitive_patterns": {{}},
                "value_hierarchy": []
            }},
            "predictive_models": {{
                "influence_levers": [],
                "conflict_triggers": []
            }}
        }}
        """
        
        response = await self.generate_response(
            prompt=profiling_prompt,
            temperature="conservative",
            thinking_level="high"
        )
        
        try:
            profile = json.loads(response['response'])
        except:
            # Fallback profile structure
            profile = {
                "person": {"name": person_name},
                "raw_analysis": response['response'],
                "status": "parsing_failed"
            }
        
        # Save to database
        await self._save_profile(person_name, profile)
        
        return profile
    
    async def _update_profile(
        self,
        person_name: str,
        conversation_data: List[Dict],
        existing_profile: Dict
    ) -> Dict:
        """Update an existing profile with new data."""
        
        formatted_data = self._format_conversations(conversation_data)
        
        update_prompt = f"""
        Existing Profile:
        {json.dumps(existing_profile, indent=2)}
        
        New Conversation Data:
        {formatted_data}
        
        Update the profile with new insights while maintaining:
        - All previous evidence traces
        - Version history
        - Confidence score adjustments
        
        Return the complete updated profile.
        """
        
        response = await self.generate_response(
            prompt=update_prompt,
            temperature="conservative",
            thinking_level="high"
        )
        
        try:
            updated_profile = json.loads(response['response'])
        except:
            # If parsing fails, merge manually
            updated_profile = existing_profile
        
        # Increment version
        updated_profile['metadata'] = updated_profile.get('metadata', {})
        updated_profile['metadata']['profile_version'] = existing_profile.get('metadata', {}).get('profile_version', 1) + 0.1
        
        # Save
        await self._save_profile(person_name, updated_profile)
        
        return updated_profile
    
    def _format_conversations(self, conversations: List[Dict]) -> str:
        """Format conversations for analysis."""
        formatted = []
        
        for conv in conversations:
            formatted.append(f"""
Conversation ID: {conv.get('id', 'unknown')}
Timestamp: {conv.get('timestamp', 'unknown')}
Content: {conv.get('content', '')}
---
""")
        
        return "\n".join(formatted)
    
    def _merge_profile_update(
        self,
        existing: Dict,
        delta: Dict
    ) -> Dict:
        """Merge delta update into existing profile."""
        # Deep merge logic
        # This is a simplified version - production needs recursive merge
        
        merged = existing.copy()
        
        # Add new observations
        if 'new_observations' in delta:
            merged.setdefault('observations', []).extend(delta['new_observations'])
        
        # Update confidence
        if 'confidence_updates' in delta:
            for key, value in delta['confidence_updates'].items():
                if key in merged.get('psychological_analysis', {}):
                    merged['psychological_analysis'][key]['confidence'] = value
        
        return merged
    
    async def _save_profile(self, person_name: str, profile: Dict):
        """Save profile to database."""
        with get_db() as db:
            # Check if exists
            existing = db.execute(
                select(Persona).where(Persona.person_name == person_name)
            ).first()
            
            if existing:
                # Update
                persona = existing[0]
                persona.profile = profile
                persona.version += 1
                persona.confidence_score = profile.get('metadata', {}).get('confidence_score', 0.5)
            else:
                # Create new
                persona = Persona(
                    person_name=person_name,
                    profile=profile,
                    confidence_score=profile.get('metadata', {}).get('confidence_score', 0.5),
                    total_references=profile.get('person', {}).get('total_references', 0)
                )
                db.add(persona)
            
            db.commit()
