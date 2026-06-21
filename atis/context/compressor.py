import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from config import settings
from retrieval.document_retriever import TargetDocument

logger = logging.getLogger("atis.compressor")

class CompressedDocument(BaseModel):
    entity: str = Field(description="Normalized name of the primary structural entity.")
    summary: str = Field(description="Condensed operational intelligence abstract.")
    key_facts: List[str] = Field(default_factory=list, description="Verified factual statements extracted from the text.")
    relationships: List[str] = Field(default_factory=list, description="Explicit relational facts identified.")

class ContextCompressor:
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client or OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)

    def compress_document(self, doc: TargetDocument) -> CompressedDocument:
        system_prompt = (
            "You are a rigid intelligence extraction service. Your task is to compress raw corporate and country intelligence files "
            "into structured JSON profiles. Retain precise metrics, ownership figures, and regulatory entities exactly as written."
        )
        user_prompt = f"Extract structured facts from this source file:\n\nPath: {doc.path}\nContent:\n{doc.content}"
        
        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=settings.LLM_TEMPERATURE
            )
            raw_content = response.choices[0].message.content
            return CompressedDocument.model_validate(json.loads(raw_content))
        except Exception as e:
            logger.error(f"Failsafe triggered during compression step on doc '{doc.id}': {str(e)}")
            # Fail-safe gracefully returns raw text indicators to protect pipeline integrity
            return CompressedDocument(
                entity=doc.name,
                summary=f"Failsafe compression fallback. Raw text length: {len(doc.content)} chars.",
                key_facts=[f"Raw extraction block: {line.strip()}" for line in doc.content.split("\n") if len(line.strip()) > 20][:5],
                relationships=[]
            )