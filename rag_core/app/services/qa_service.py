"""Enhanced QA Service for SATIM and International Standards Comparison"""

import datetime
from app.services.llm.factory import create_llm
from config.settings import TOP_N_RESULTS
import logging
from typing import List, Dict, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class QAService:
    def __init__(self, satim_search_service, intl_search_service):
        """
        Initialize the QA service with search services and LLM
        
        Args:
            satim_search_service: SearchService for SATIM database
            intl_search_service: SearchService for international standards
        """
        self.model = create_llm()
        self.satim_search = satim_search_service
        self.intl_search = intl_search_service
        self.min_confidence = 0.5  # Minimum confidence score for results

    def preprocess_use_case(self, use_case: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        Enhanced preprocessing with better error handling and logging
        """
        # Default response for empty history
        if not conversation_history:
            return {
                "processed_use_case": use_case,
                "is_continuation": False,
                "is_secure": True
            }
        
        try:
            prompt = self._build_preprocessing_prompt(use_case, conversation_history)
            response = self.model.generate_content(prompt)
            response_text = response.text

            # Safer response parsing
            is_continuation = "true" in response_text.lower().split("is_continuation:")[1].split()[0].lower() if "is_continuation:" in response_text else False
            is_secure = "false" not in response_text.lower().split("is_secure:")[1].split()[0].lower() if "is_secure:" in response_text else True
            
            processed_use_case = use_case
            if "processed_use_case:" in response_text:
                processed_part = response_text.split("processed_use_case:")[1].split("\n")[0].strip()
                if processed_part:
                    processed_use_case = processed_part

            return {
                "processed_use_case": processed_use_case,
                "is_continuation": is_continuation,
                "is_secure": is_secure
            }
            
        except Exception as e:
            logger.error(f"Preprocessing error: {str(e)}", exc_info=True)
            return {
                "processed_use_case": use_case,
                "is_continuation": False,
                "is_secure": False
            }

    def generate_comparative_analysis(self, use_case: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        Main analysis workflow with enhanced error handling and logging
        """
        # Preprocess with security check
        analysis = self.preprocess_use_case(use_case, conversation_history)
        if not analysis["is_secure"]:
            logger.warning(f"Blocked insecure query: {use_case[:50]}...")
            return {
                "answer": "Request blocked due to security policy.",
                "status": "rejected",
                "security_flag": True
            }

        try:
            # Get results from both sources
            satim_results = self._get_search_results(
                self.satim_search, 
                analysis["processed_use_case"], 
                "SATIM"
            )
            intl_results = self._get_search_results(
                self.intl_search,
                analysis["processed_use_case"],
                "International"
            )

            # Generate analysis
            return self._generate_analysis_response(
                use_case=analysis["processed_use_case"],
                satim_results=satim_results,
                intl_results=intl_results,
                conversation_history=conversation_history,
                is_continuation=analysis["is_continuation"]
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            return {
                "answer": "System error during analysis.",
                "status": "error",
                "error": str(e),
                "is_continuation": analysis.get("is_continuation", False)
            }

    def _get_search_results(self, search_service, query: str, source: str) -> List[Tuple[str, float]]:
        """Safe search execution with logging"""
        try:
            results = search_service.search(query, TOP_N_RESULTS)
            logger.info(f"Found {len(results)} {source} results for query: {query[:50]}...")
            return [(chunk, score) for chunk, score in results if score >= self.min_confidence]
        except Exception as e:
            logger.error(f"{source} search failed: {str(e)}")
            return []

    def _generate_analysis_response(self, use_case: str, satim_results: List[Tuple[str, float]], 
                                  intl_results: List[Tuple[str, float]], conversation_history: Optional[List[Dict]],
                                  is_continuation: bool) -> Dict:
        """Generate the final analysis response"""
        # Prepare chunks
        satim_chunks = [chunk for chunk, _ in satim_results]
        intl_chunks = [chunk for chunk, _ in intl_results]

        # Handle empty results
        if not satim_chunks and not intl_chunks:
            return {
                "answer": "No relevant policies or standards found.",
                "status": "no_results",
                "is_continuation": is_continuation
            }

        # Generate analysis
        prompt = self._build_analysis_prompt(
            use_case=use_case,
            satim_chunks=satim_chunks,
            intl_chunks=intl_chunks,
            conversation_history=conversation_history,
            is_continuation=is_continuation
        )
        
        response = self.model.generate_content(prompt)
        
        return {
            "answer": response.text,
            "status": "success",
            "is_continuation": is_continuation,
            "context": {
                "satim": satim_chunks,
                "international": intl_chunks
            },
            "scores": {
                "satim": [float(score) for _, score in satim_results],
                "international": [float(score) for _, score in intl_results]
            }
        }

    def _build_preprocessing_prompt(self, use_case: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Build the preprocessing prompt to determine context and security
        """
        context = self._build_conversation_context(conversation_history) if conversation_history else ""

        prompt = f"""
Analyze this use case for security and context:

USE CASE:
{use_case}

{context if context else ""}

Please provide:
is_continuation: [true/false] - Is this related to previous conversation?
is_secure: [true/false] - Does this contain any security risks?
processed_use_case: [processed text] - Clean version of the use case
"""
        return prompt



    def _build_analysis_prompt(self, use_case: str, satim_chunks: List[str], intl_chunks: List[str],
                             conversation_history: Optional[List[Dict]], is_continuation: bool) -> str:
        """
        Build the comparative analysis prompt with clear formatting
        """
        context = self._build_conversation_context(conversation_history) if conversation_history else ""

        prompt = f"""

    USE CASE:
    {use_case}

    {'(Note: This is a continuation of previous discussion)\\n' if is_continuation else ''}

    SATIM POLICIES:
    {satim_chunks[0] if satim_chunks else "No relevant SATIM policies found"}

    INTERNATIONAL STANDARDS:
    {intl_chunks[0] if intl_chunks else "No relevant international standards found"}

    {context}

    Please provide your analysis in this exact format:

                             COMPLIANCE SUMMARY
    SATIM Status:
    [Brief summary of SATIM compliance]

    International Status:
    [Brief summary of international standards compliance]

                               KEY FINDINGS
    [List 3-5 main compliance gaps, each on a new line with centered bullets]

                             REQUIRED ACTIONS
    [List prioritized actions, numbered 1-5, each on a new line]


    """
        return prompt


    def _build_conversation_context(self, conversation_history: Optional[List[Dict]]) -> str:
        """Build conversation context string if available"""
        if not conversation_history:
            return ""

        context = "## Conversation Context:\n"
        for msg in conversation_history[-3:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n"
        return context