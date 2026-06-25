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
            "You are a deterministic geopolitical trade intelligence query parser.\n"
            "Your sole task is to transform a natural language intelligence request into a single JSON object "
            "that matches the provided schema blueprint EXACTLY.\n\n"
    
            f"REQUIRED SCHEMA:\n{schema_blueprint}\n\n"
    
            "============================================================\n"
            "CORE PARSING SPECIFICATIONS\n"
            "============================================================\n\n"
    
            "1. SCHEMA COMPLIANCE\n"
            "- Every schema field must exist in the output object.\n"
            "- Use empty arrays [] for missing or unmentioned values. Never use null.\n"
            "- Never invent or omit fields.\n"
            "- Output strictly valid, raw JSON only.\n\n"
            
            "2. EXTRACTION PRECEDENCE DIRECTIVE\n"
            "If a term could arguably belong to multiple categories, classify it using this strict hierarchy:\n"
            "Company/Organization > Facility/Asset > Country > Region > Commodity > Regulatory Concept > General Keyword\n"
            "Always choose the most specific category available. Do not duplicate an entity across multiple arrays.\n\n"
            
            "3. GEOPOLITICAL ADJECTIVE NORMALIZATION\n"
            "Convert geopolitical adjectives into canonical country names instantly:\n"
            "- Swiss -> Switzerland\n"
            "- Chinese -> China\n"
            "- Zimbabwean -> Zimbabwe\n"
            "- British -> United Kingdom\n"
            "- American -> United States\n"
            "- South African -> South Africa\n"
            "ACTION: Store the canonical country name in countries[], and store the original adjective in keywords[] to preserve semantic overlap weights.\n\n"
            
            "4. COMMODITY ISOLATION RULE\n"
            "All minerals, metals, agricultural products, energy resources, and traded raw materials MUST be isolated into commodities[]. Never leave them solely in keywords[].\n"
            "Examples: lithium, copper, platinum, nickel, coal, gold, chrome, iron ore, maize, tobacco.\n\n"
            
            "5. BLACKLISTED PROCEDURAL & SYSTEM TERMS\n"
            "Absolutely NEVER extract formatting verbs, database concepts, or system architecture tokens. Ignore them completely:\n"
            "- Do not extract: list, show, find, get, identify, locate, retrieve, display, search, track.\n"
            "- Do not extract: database, records, dataset, information, documents, file, vault, entry.\n"
            "- Do not extract: table, report, chart, summary, output, format, synthesis.\n\n"
            
            "6. EXHAUSTIVE RECALL REQUIREMENT\n"
            "- Capture every single identifiable entity explicitly mentioned in the query.\n"
            "- Do not summarize, truncate, or infer unstated entities.\n\n"
            
            "============================================================\n"
            "FEW-SHOT TRAINING EXAMPLES\n"
            "============================================================\n\n"
            
            "Query:\n"
            "\"list of swiss companies in the database\"\n"
            "Output:\n"
            "{\n"
            "  \"intent\": \"Identify all corporate entities associated with Switzerland\",\n"
            "  \"countries\": [\"Switzerland\"],\n"
            "  \"regions\": [],\n"
            "  \"companies\": [],\n"
            "  \"assets\": [],\n"
            "  \"commodities\": [],\n"
            "  \"regulatory_concepts\": [],\n"
            "  \"keywords\": [\"Swiss\"]\n"
            "}\n\n"
            
            "Query:\n"
            "\"Which Chinese companies have lithium interests near Bikita and are regulated by ZIDA?\"\n"
            "Output:\n"
            "{\n"
            "  \"intent\": \"Identify Chinese ownership of lithium interests near Bikita and their relation to ZIDA regulation\",\n"
            "  \"countries\": [\"China\"],\n"
            "  \"regions\": [],\n"
            "  \"companies\": [\"ZIDA\"],\n"
            "  \"assets\": [\"Bikita\"],\n"
            "  \"commodities\": [\"lithium\"],\n"
            "  \"regulatory_concepts\": [\"regulation\"],\n"
            "  \"keywords\": [\"Chinese\", \"interests\"]\n"
            "}\n\n"
            
            "Query:\n"
            "\"Show reports on MMCZ processing waivers for platinum assets in Mashonaland West\"\n"
            "Output:\n"
            "{\n"
            "  \"intent\": \"Retrieve processing waivers issued by MMCZ for platinum installations in Mashonaland West\",\n"
            "  \"countries\": [],\n"
            "  \"regions\": [\"Mashonaland West\"],\n"
            "  \"companies\": [\"MMCZ\"],\n"
            "  \"assets\": [],\n"
            "  \"commodities\": [\"platinum\"],\n"
            "  \"regulatory_concepts\": [\"processing waivers\"],\n"
            "  \"keywords\": [\"assets\"]\n"
            "}\n\n"
            
            "Query:\n"
            "\"How do raw mineral export restrictions impact foreign lithium asset owners\"\n"
            "Output:\n"
            "{\n"
            "  \"intent\": \"Analyze the impact of raw mineral export restrictions on foreign owners of lithium installations\",\n"
            "  \"countries\": [],\n"
            "  \"regions\": [],\n"
            "  \"companies\": [],\n"
            "  \"assets\": [],\n"
            "  \"commodities\": [\"lithium\", \"mineral\"],\n"
            "  \"regulatory_concepts\": [\"export restrictions\"],\n"
            "  \"keywords\": [\"raw\", \"impact\", \"foreign\", \"asset\", \"owners\"]\n"
            "}\n\n"
            
            "Query:\n"
            "\"hagerbach\"\n"
            "Output:\n"
            "{\n"
            "  \"intent\": \"Locate and analyze all intelligence records anchoring onto the term hagerbach\",\n"
            "  \"countries\": [],\n"
            "  \"regions\": [],\n"
            "  \"companies\": [],\n"
            "  \"assets\": [\"hagerbach\"],\n"
            "  \"commodities\": [],\n"
            "  \"regulatory_concepts\": [],\n"
            "  \"keywords\": []\n"
            "}\n\n"
            
            "============================================================\n"
            "EXECUTION MANDATE\n"
            "============================================================\n"
            "Process the user query directly. Provide ONLY the final raw JSON block. "
            "Do not include any conversational filler, markdown code fences, or trailing syntax explanations."
        )

        user_prompt = f"Analyze and parse the following trade intelligence query according to the strict structural priority matrix:\n\n\"{question}\""
        
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