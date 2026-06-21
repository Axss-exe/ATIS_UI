# atis/reasoning/reasoning_engine.py
from typing import Optional
from openai import OpenAI
from atis.config import settings

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