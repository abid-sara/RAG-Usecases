"""Base class for LLM implementations"""

from abc import ABC, abstractmethod

class BaseLLM(ABC):
    """Abstract base class for language model implementations"""
    
    @abstractmethod
    def generate_content(self, prompt):
        """
        Generate text content from a prompt
        
        Args:
            prompt (str): The input prompt
            
        Returns:
            object: Response with a text attribute
        """
        pass