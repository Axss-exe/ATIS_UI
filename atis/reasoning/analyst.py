import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from config import settings
from context.evidence_builder import EvidencePackage

logger = logging.getLogger("atis.analyst")

class ATISReport(BaseModel):
    executive_summary: str = Field(description="High-level analytical briefing.")
    key_actors: List[str] = Field(description="Primary groups, persons, or corporate entities identified.")
    relationships_mapped: List[str] = Field(description="Explicitly verified graph alignments.")
    opportunities: List[str] = Field(description="Commercial advantages or operational insights.")
    risks: List[str] = Field(description="Regulatory, political, or sovereign hazards.")
    regulatory_considerations: List[str] = Field(description="Enforcement dynamics and oversight rules.")
    intelligence_gaps: List[str] = Field(description="Identified areas with missing or partial data.")
    sources_used: List[str] = Field(description="Citations matching source data file locations.")

class AnalystEngine:
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client or OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)

    def synthesize_report(self, package: EvidencePackage) -> ATISReport:
        system_prompt = (
            "You are a rigorous trade intelligence analyst for the Africa Trade & Intelligence System (ATIS). "
            "You write highly technical briefing papers based *only* on the verified evidence packages provided. "
            "Never extrapolate or hallucinate facts beyond what is explicitly cited in the data packages. "
            "Output a clean JSON object that matches the requested schema without any markdown formatting."
        )
        
        user_prompt = (
            f"Analyze the following intelligence requirements: {package.question}\n\n"
            f"EVIDENCE DOSSIER:\n"
            f"Core Entities: {json.dumps(package.entities)}\n"
            f"Structural Graph Links: {json.dumps([e.model_dump() for e in package.relationships])}\n"
            f"Verified Core Facts: {json.dumps([f.model_dump() for f in package.facts])}\n"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "system_prompt"},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=settings.LLM_TEMPERATURE
            )
            raw_content = response.choices[0].message.content
            return ATISReport.model_validate(json.loads(raw_content))
        except Exception as e:
            logger.error(f"Critical breakdown during Analyst Synthesis engine execution: {str(e)}")
            raise e