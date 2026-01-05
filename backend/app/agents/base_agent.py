"""
Base agent class and shared utilities for all AI agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.gemini_client import gemini_client
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""
    
    def __init__(self, name: str, system_instruction: str):
        """
        Initialize the agent.
        
        Args:
            name: Agent name for logging
            system_instruction: System prompt that defines agent behavior
        """
        self.name = name
        self.system_instruction = system_instruction
        self.gemini = gemini_client
        logger.info(f"Initialized {name} agent")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and generate output.
        
        Args:
            input_data: Input data specific to the agent
            
        Returns:
            Agent output
        """
        pass
    
    async def generate_response(
        self,
        prompt: str,
        temperature: str = "balanced",
        thinking_level: str = "high",
        include_thoughts: bool = False
    ) -> Dict[str, str]:
        """
        Generate a response using Gemini with the agent's system instruction.
        
        Args:
            prompt: User query or task
            temperature: 'conservative', 'balanced', or 'creative'
            thinking_level: Depth of reasoning
            include_thoughts: Whether to return chain of thought
            
        Returns:
            Dict with 'thought' and 'response' keys
        """
        logger.debug(f"{self.name} generating response with {thinking_level} thinking")
        
        response = await self.gemini.generate_with_thinking(
            prompt=prompt,
            system_instruction=self.system_instruction,
            thinking_level=thinking_level,
            include_thoughts=include_thoughts,
            temperature=temperature
        )
        
        return response
    
    async def generate_stream(
        self,
        prompt: str,
        temperature: str = "balanced"
    ):
        """
        Generate streaming response.
        
        Yields text chunks as they're generated.
        """
        logger.debug(f"{self.name} generating streaming response")
        
        async for chunk in self.gemini.generate_stream(
            prompt=prompt,
            system_instruction=self.system_instruction,
            temperature=temperature
        ):
            yield chunk
    
    def log_action(self, action: str, details: Optional[Dict] = None):
        """Log agent actions for debugging."""
        log_msg = f"{self.name}: {action}"
        if details:
            log_msg += f" - {details}"
        logger.info(log_msg)
