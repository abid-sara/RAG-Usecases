import requests
from config.settings import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL_NAME, JWT_TOKEN, TEMPERATURE, MAX_TOKENS
from app.services.llm.base import BaseLLM
import regex as re

class DeepSeekLLM(BaseLLM):
    """DeepSeek LLM implementation"""
    
    def __init__(self):
        """Initialize the DeepSeek client"""
        self.base_url = DEEPSEEK_BASE_URL
        self.model_name = DEEPSEEK_MODEL_NAME
        self.token = JWT_TOKEN
        self.temperature = TEMPERATURE
        self.max_tokens = MAX_TOKENS
    
    def generate_content(self, prompt):
        """
        STRICT Arabic-only DeepSeek implementation
        - Forces Arabic responses
        - Eliminates <think> tags
        - Blocks English leakage
        - Removes Chinese/other symbols
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # STRICT ARABIC INSTRUCTIONS (3-layer enforcement)
        system_msg = """⚠️ توجيهات صارمة:
    1. ممنوع استخدام أي لغة غير العربية
    2. ممنوع كتابة أي تحليل داخلي مرئي
    3. الإجابة يجب أن تكون مباشرة دون مقدمات
    4. ممنوع استخدام علامات <think> أو أي كلمات إنجليزية
    5. إذا لم تتبع هذه التعليمات ستفشل المهمة"""

        user_prompt = f"""[إجابة عربية فقط]
    [بدون أي كلمات إنجليزية]
    [بدون تحليل مسبق]

    {prompt}"""

        payload = {
            "model": "deepseek-r1:70b",
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,  # Very low for deterministic output
            "max_tokens": self.max_tokens,
            "parameters": {
                "language": {
                    "enforcement": "strict",
                    "allowed": ["ar"],
                    "fallback": None
                },
                "response_mode": "direct",
                "disable_reasoning": True
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            # Advanced cleaning pipeline
            content = response.json()["choices"][0]["message"]["content"]
            
            # 1. Remove all non-Arabic text
            arabic_only = re.sub(
                r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF،؛؟٠-٩\s\.\,\!\-]', 
                '', 
                content
            )
            
            # 2. Remove residual tags
            clean_content = re.sub(r'<think>|<\/think>|Okay,|so|first', '', arabic_only)
            
            # 3. Ensure starts with Arabic
            if clean_content.strip():
                if not any('\u0600' <= char <= '\u06FF' for char in clean_content[:10]):
                    # Find first Arabic character
                    arabic_start = next(
                        (i for i, char in enumerate(clean_content) 
                        if '\u0600' <= char <= '\u06FF')
                    )
                    clean_content = clean_content[arabic_start:]
            
            class Response:
                def __init__(self, text):
                    self.text = text
                    
            return Response(clean_content.strip())
            
        except Exception as e:
            error_msg = f"DeepSeek error: {str(e)}"
            if 'response' in locals():
                error_msg += f"\nRaw response: {response.text[:300]}"
            raise Exception(error_msg)