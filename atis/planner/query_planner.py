# atis/planner/query_planner.py
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI

# Standardized absolute package import
from atis.config import settings

logger = logging.getLogger("atis.planner")

class RetrievalPlan(BaseModel):
    intent: str = Field(description="The core objective of the intelligence investigation.")
    
    # --- GRAPH SEED EXTRACTION BUCKETS ---
    countries: List[str] = Field(default_factory=list, description="Target nations extracted from user input (e.g., Zimbabwe, China).")
    locations: List[str] = Field(default_factory=list, description="Specific regional provinces, zones, or cities (e.g., Masvingo, Beijing).")
    companies: List[str] = Field(default_factory=list, description="Specific named companies, corporations, or state-owned enterprises (e.g., Sinosteel, Bikita Minerals).")
    assets: List[str] = Field(default_factory=list, description="Specific named physical projects, mines, plants, or infrastructure assets.")
    keywords: List[str] = Field(default_factory=list, description="Crucial context tokens, adjectives, or operational terms (e.g., state-backed, lithium, licenses).")
    
    # --- CLASSIFICATION & ROUTING ---
    entity_types: List[str] = Field(default_factory=list, description="Target structural types to find: company, project, regulator, law.")
    topics: List[str] = Field(default_factory=list, description="Target domains or commodities, e.g., lithium, gold, tax.")
    required_relationships: List[str] = Field(default_factory=list, description="Logical verbs mapping connections, e.g., owned_by, regulated_by.")
    search_queries: List[str] = Field(default_factory=list, description="Optimized, distinct search queries for matching indices.")

class QueryPlanner:
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client or OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)

    def generate_plan(self, question: str) -> RetrievalPlan:
        # Dynamically extract the blueprint Pydantic expects
        schema_blueprint = json.dumps(RetrievalPlan.model_json_schema(), indent=2)

        system_prompt = (
            "You are an expert geopolitical trade intelligence query router. Your sole task is to analyze analytical questions "
            "and output a strictly valid JSON object that adheres EXACTLY to the following JSON schema blueprint.\n\n"
            f"REQUIRED SCHEMA:\n{schema_blueprint}\n\n"
            "Extract specific proper nouns (companies, assets, locations) into their dedicated arrays. "
            "Do not include markdown formatting, code blocks (such as ```json), or conversational text. Output only the raw JSON."
        )
        user_prompt = f"Deconstruct the following intelligence request into structural search variables:\n\n\"{question}\""
        
        retries = 0
        while retries < settings.LLM_MAX_RETRIES:
            try:
                response = self.client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=settings.LLM_TEMPERATURE,
                    extra_body={
                        "reasoning_effort": "low" # Keeps the extraction fast and deterministic
                    }
                )
                raw_content = response.choices[0].message.content
                if not raw_content:
                    raise ValueError("Received an empty response from the LLM provider.")
                
                parsed_json = json.loads(raw_content)
                return RetrievalPlan.model_validate(parsed_json)
            except Exception as e:
                retries += 1
                logger.warning(f"QueryPlanner fault encountered: {str(e)}. Retrying ({retries}/{settings.LLM_MAX_RETRIES}).")
                if retries >= settings.LLM_MAX_RETRIES:
                    logger.error("QueryPlanner has exhausted all configured system execution retries.")
                    raise e