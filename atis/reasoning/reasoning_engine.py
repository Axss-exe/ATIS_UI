# atis/reasoning/reasoning_engine.py
import json
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
from atis.config import settings

logger = logging.getLogger("atis.reasoning")

class ReasoningEngine:
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client or OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)

    def synthesize_final_response(self, original_question: str, structured_context: str) -> str:
        system_prompt = (
            "You are a senior trade intelligence analyst. Your objective is to answer user inquiries "
            "using ONLY the verified context block provided. Do not extrapolate, assume, or bring in outside information. "
            "State your findings clearly, highlighting confirmed corporate ownership networks and regulatory bodies."
        )
        
        user_prompt = (
            f"VERIFIED CONTEXT RECORDS:\n{structured_context}\n\n"
            f"USER REQUIREMENT:\n\"{original_question}\"\n\n"
            "Synthesize the final analytical response:"
        )

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Kept low for high fidelity/no hallucinations
            extra_body={"reasoning_effort": "low"}
        )
        
        return response.choices[0].message.content or "Error generating final response synthesis."

    def extract_structured_cards(self, original_question: str, markdown_report: str) -> Dict[str, Any]:
        """
        Parses the finalized markdown strategic report into structured UI components 
        using JSON object mode to safely deliver cleanly mapped data structures to the frontend.
        """
        system_prompt = (
            "You are a specialized data structure extractor. Your sole job is to read an intelligence "
            "report and decompose it into a clean, well-formed JSON object matching the exact keys requested. "
            "Do not introduce outside details or create facts not explicitly supported by the report text."
        )
        
        user_prompt = (
            f"ORIGINAL USER INQUIRY: \"{original_question}\"\n\n"
            f"MARKDOWN INTELLIGENCE REPORT:\n{markdown_report}\n\n"
            "Deconstruct the report text above and populate the following JSON schema architecture precisely:\n"
            "{\n"
            "  \"summary\": [\"list of high-level key bullet points or core analytical takeaways from the report\"],\n"
            "  \"opportunities\": [{\"title\": \"string title\", \"description\": \"string detail\"}],\n"
            "  \"risks\": [{\"title\": \"string title\", \"description\": \"string detail\"}],\n"
            "  \"recommendations\": [{\"title\": \"string title\", \"description\": \"string detail\"}],\n"
            "  \"tables\": []\n"
            "}\n"
        )

        # Fail-safe default schema payload to guarantee runtime safety if an exception triggers
        fallback_payload = {
            "summary": ["Strategic intelligence report compiled successfully."],
            "opportunities": [],
            "risks": [],
            "recommendations": [],
            "tables": []
        }

        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content
            if not raw_content:
                return fallback_payload
                
            parsed_json = json.loads(raw_content)
            
            # Ensure all downstream keys exist defensively even if LLM misses one
            for key in fallback_payload:
                if key not in parsed_json:
                    parsed_json[key] = fallback_payload[key]
                    
            return parsed_json

        except Exception as e:
            logger.error(f"Failed to extract structured interface cards from markdown report: {str(e)}")
            return fallback_payload