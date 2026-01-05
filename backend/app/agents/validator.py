"""
Validator Agent - Pre-ingestion contradiction and hallucination detection.
Analyzes documents before they enter the database to flag discrepancies.
"""

from typing import Dict, Any, List, Optional
from app.agents.base_agent import BaseAgent
from app.gemini_client import gemini_client
from app.llama_embeddings import get_llama_client
from app.database import get_db
from app.models import Conflict
from sqlalchemy import select
import json
import logging

logger = logging.getLogger(__name__)


VALIDATOR_SYSTEM_PROMPT = """
You are a Forensic Data Validator with expertise in:
- Logical consistency analysis
- Contradiction detection across large documents
- Hallucination identification in LLM-generated content
- Timeline verification and fact-checking

Your ONLY task: Analyze documents for internal contradictions and conflicts with existing data.

Requirements:

1. **Internal Consistency Check:**
   - Scan each document for self-contradictions
   - Flag statements that contradict other statements in the same document
   - Detect logical impossibilities (timeline conflicts, mutually exclusive claims)
   - Identify vague or ambiguous statements that could cause downstream issues

2. **Cross-Document Validation:**
   - Compare new documents against existing database facts
   - Flag contradictions with previously ingested information
   - Detect evolving positions (flag as "evolution" not contradiction if justified)
   - Identify duplicate information with slight variations

3. **Hallucination Detection:**
   - Flag suspiciously specific details without source attribution
   - Detect common LLM hallucination patterns (invented citations, fake data)
   - Identify overly confident claims without evidence
   - Flag statements that seem inconsistent with conversation context

4. **Output Format:**
   Return JSON array of discrepancies:
   ```json
   [
     {
       "type": "self_contradiction|cross_contradiction|hallucination|ambiguity",
       "severity": "minor|moderate|critical",
       "location": {
         "document_id": "...",
         "section": "line 45-47 or paragraph 3",
         "excerpt": "exact contradicting text"
       },
       "conflict_with": {
         "document_id": "..." or "same_document",
         "excerpt": "conflicting statement"
       },
       "explanation": "detailed explanation of the issue",
       "suggested_resolution": "how to resolve this",
       "requires_user_input": true/false
     }
   ]
   ```

5. **Classification Rules:**
   - **Critical**: Factual contradictions that would corrupt the knowledge base
   - **Moderate**: Ambiguous statements or timeline inconsistencies
   - **Minor**: Stylistic differences or evolution in thinking

Constraint: NO false positives. Only flag genuine issues. Distinguish between:
- Evolution of thought (acceptable)
- Contradictory facts (unacceptable)
"""


class ValidatorAgent(BaseAgent):
    """
    The Validator Agent performs pre-ingestion validation.
    It checks documents for contradictions before they enter the system.
    """
    
    def __init__(self):
        super().__init__(
            name="Validator",
            system_instruction=VALIDATOR_SYSTEM_PROMPT
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and validate documents.
        
        Args:
            input_data: Must contain 'documents' key with list of documents
            
        Returns:
            Validation results
        """
        documents = input_data.get('documents', [])
        check_against_existing = input_data.get('check_against_existing', True)
        
        return await self.validate_documents(documents, check_against_existing)
    
    async def validate_documents(
        self,
        documents: List[Dict[str, Any]],
        check_against_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Validate documents for contradictions and hallucinations.
        
        Args:
            documents: List of documents to validate, each with:
                - id: Document identifier
                - content: Text content
                - metadata: Optional metadata
            check_against_existing: Whether to check against existing DB data
            
        Returns:
            Validation report with all detected issues
        """
        self.log_action("Starting document validation", {
            "document_count": len(documents),
            "check_existing": check_against_existing
        })
        
        all_discrepancies = []
        
        # Step 1: Check each document for internal consistency
        for doc in documents:
            internal_issues = await self._check_internal_consistency(doc)
            all_discrepancies.extend(internal_issues)
        
        # Step 2: Check cross-document contradictions
        if len(documents) > 1:
            cross_issues = await self._check_cross_document_consistency(documents)
            all_discrepancies.extend(cross_issues)
        
        # Step 3: Check against existing database (if requested)
        if check_against_existing:
            for doc in documents:
                db_issues = await self._check_against_database(doc)
                all_discrepancies.extend(db_issues)
        
        # Step 4: Categorize and prioritize
        report = self._generate_report(all_discrepancies)
        
        self.log_action("Validation complete", {
            "total_issues": len(all_discrepancies),
            "critical": report['summary']['critical'],
            "moderate": report['summary']['moderate'],
            "minor": report['summary']['minor']
        })
        
        return report
    
    async def _check_internal_consistency(
        self,
        document: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check a single document for internal contradictions."""
        
        content = document.get('content', '')
        doc_id = document.get('id', 'unknown')
        
        # Split large documents into chunks for analysis
        chunks = self._chunk_document(content)
        
        validation_prompt = f"""
        Analyze this document for internal contradictions and logical inconsistencies.
        
        Document ID: {doc_id}
        Content:
        {content[:15000]}  # Limit to 15k chars for single analysis
        
        Find:
        1. Statements that directly contradict other statements
        2. Timeline inconsistencies
        3. Logical impossibilities
        4. Suspicious claims that seem like hallucinations
        5. Ambiguous statements that could cause confusion
        
        Return JSON array of issues (empty array if none found).
        """
        
        response = await self.generate_response(
            prompt=validation_prompt,
            thinking_level="high",
            temperature="conservative"
        )
        
        try:
            issues = json.loads(response['response'])
            
            # Add document context to each issue
            for issue in issues:
                issue['document_id'] = doc_id
                if 'location' not in issue:
                    issue['location'] = {'document_id': doc_id}
                    
            return issues if isinstance(issues, list) else []
        except Exception as e:
            logger.warning(f"Failed to parse validation response: {e}")
            return []
    
    async def _check_cross_document_consistency(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check for contradictions across multiple documents."""
        
        # Create document summaries for comparison
        doc_summaries = []
        for doc in documents:
            doc_summaries.append({
                'id': doc.get('id', 'unknown'),
                'content': doc.get('content', '')[:5000]  # First 5k chars
            })
        
        cross_check_prompt = f"""
        Compare these documents for contradictions and inconsistencies.
        
        Documents:
        {json.dumps(doc_summaries, indent=2)}
        
        Find:
        1. Facts that contradict between documents
        2. Timeline conflicts
        3. Duplicate information with slight variations
        4. Evolution in thinking (note as "evolution" not contradiction)
        
        Return JSON array of cross-document issues.
        """
        
        response = await self.generate_response(
            prompt=cross_check_prompt,
            thinking_level="high",
            temperature="conservative"
        )
        
        try:
            issues = json.loads(response['response'])
            return issues if isinstance(issues, list) else []
        except:
            return []
    
    async def _check_against_database(
        self,
        document: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check document against existing database facts."""
        
        content = document.get('content', '')
        doc_id = document.get('id', 'unknown')
        
        # Extract key claims from the document
        extraction_prompt = f"""
        Extract the top 10 most important factual claims from this document.
        
        Document:
        {content[:10000]}
        
        Return JSON array of claims (just the text of each claim).
        """
        
        response = await self.generate_response(
            prompt=extraction_prompt,
            thinking_level="medium",
            temperature="conservative"
        )
        
        try:
            claims = json.loads(response['response'])
        except:
            return []
        
        # Check each claim against database
        issues = []
        with get_db() as db:
            # Get existing conflicts from database
            existing_conflicts = db.execute(
                select(Conflict).where(Conflict.resolved == False)
            ).fetchall()
            
            # Get Llama embedding client
            llama_client = get_llama_client()
            
            for claim in claims:
                # Embed claim and search for similar facts using Llama
                claim_embedding = llama_client.embed_text(str(claim))
                
                # This would use vector DB to find similar statements
                # For now, we'll check against existing unresolved conflicts
                for conflict_row in existing_conflicts:
                    conflict = conflict_row[0]
                    
                    # Use LLM to check if claim conflicts with known conflict
                    conflict_check = f"""
                    Does this new claim contradict either of these existing conflicting statements?
                    
                    New Claim: {claim}
                    Existing Conflict A: {conflict.old_value}
                    Existing Conflict B: {conflict.new_value}
                    
                    Return JSON:
                    {{
                        "conflicts": true/false,
                        "explanation": "...",
                        "severity": "minor|moderate|critical"
                    }}
                    """
                    
                    check_response = await gemini_client.generate_flash(
                        conflict_check,
                        response_format="json"
                    )
                    
                    try:
                        result = json.loads(check_response)
                        if result.get('conflicts'):
                            issues.append({
                                'type': 'cross_contradiction',
                                'severity': result.get('severity', 'moderate'),
                                'location': {
                                    'document_id': doc_id,
                                    'excerpt': str(claim)
                                },
                                'conflict_with': {
                                    'document_id': 'existing_database',
                                    'conflict_id': str(conflict.id),
                                    'excerpt': conflict.old_value
                                },
                                'explanation': result.get('explanation', ''),
                                'requires_user_input': True
                            })
                    except:
                        pass
        
        return issues
    
    def _chunk_document(self, content: str, chunk_size: int = 5000) -> List[str]:
        """Split large documents into analyzable chunks."""
        chunks = []
        words = content.split()
        
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _generate_report(self, discrepancies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive validation report."""
        
        # Categorize by severity
        critical = [d for d in discrepancies if d.get('severity') == 'critical']
        moderate = [d for d in discrepancies if d.get('severity') == 'moderate']
        minor = [d for d in discrepancies if d.get('severity') == 'minor']
        
        # Group by type
        by_type = {}
        for d in discrepancies:
            dtype = d.get('type', 'unknown')
            by_type.setdefault(dtype, []).append(d)
        
        # Filter items requiring user input
        requires_action = [d for d in discrepancies if d.get('requires_user_input')]
        
        return {
            'summary': {
                'total_issues': len(discrepancies),
                'critical': len(critical),
                'moderate': len(moderate),
                'minor': len(minor),
                'requires_user_action': len(requires_action)
            },
            'by_severity': {
                'critical': critical,
                'moderate': moderate,
                'minor': minor
            },
            'by_type': by_type,
            'action_required': requires_action,
            'all_discrepancies': discrepancies
        }
    
    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        correct_value: Optional[str] = None
    ) -> bool:
        """
        Mark a conflict as resolved with user's decision.
        
        Args:
            conflict_id: ID of the conflict to resolve
            resolution: User's explanation of resolution
            correct_value: The correct value (if applicable)
        """
        with get_db() as db:
            conflict = db.get(Conflict, conflict_id)
            if conflict:
                conflict.resolved = True  # type: ignore
                conflict.resolution = resolution  # type: ignore
                if correct_value:
                    conflict.new_value = correct_value  # type: ignore
                db.commit()
                return True
        return False


# Global instance
validator_agent = ValidatorAgent()
