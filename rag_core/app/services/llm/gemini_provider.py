"""Gemini LLM provider implementation"""

import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL_NAME, TEMPERATURE, MAX_TOKENS
from app.services.llm.base import BaseLLM

class GeminiLLM(BaseLLM):
    """Google Gemini LLM implementation"""
    
    def __init__(self):
        """Initialize the Gemini model"""
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            generation_config={
                "temperature": TEMPERATURE,
                "max_output_tokens": MAX_TOKENS,
            }
        )
    
    def generate_content(self, prompt):
        """
        Generate content using Gemini
        
        Args:
            prompt (str): The input prompt
            
        Returns:
            Response object with text attribute
        """
        return self.model.generate_content(prompt)