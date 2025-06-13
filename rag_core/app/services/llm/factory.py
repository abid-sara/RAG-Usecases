"""Factory for creating LLM instances"""

import logging
from config.settings import LLM_PROVIDER

logger = logging.getLogger("app.services.llm.factory")

def create_llm():
    """
    Create and return the appropriate LLM based on configuration
    
    Returns:
        BaseLLM: An instance of the configured LLM provider
    """
    # Clean the provider value to handle potential comment inclusion
    provider_value = LLM_PROVIDER.strip()
    
    # Remove any comments (text after #)
    if '#' in provider_value:
        provider_value = provider_value.split('#')[0].strip()
    
    # Log for debugging
    logger.info(f"Creating LLM with provider: '{provider_value}'")
    
    if provider_value.lower() == "gemini":
        from app.services.llm.gemini_provider import GeminiLLM
        return GeminiLLM()
    elif provider_value.lower() == "deepseek":
        from app.services.llm.deepseek_provider import DeepSeekLLM
        return DeepSeekLLM()
    else:
        # Fallback to DeepSeek if provider is invalid
        logger.warning(f"Invalid provider '{provider_value}', falling back to DeepSeek")
        from app.services.llm.deepseek_provider import DeepSeekLLM
        return DeepSeekLLM()