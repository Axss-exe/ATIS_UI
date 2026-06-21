from typing import List, Dict, Any
from pydantic import BaseModel
from config import settings
from graph.relationship_expander import GraphEdge
from context.compressor import CompressedDocument

class EvidencePackage(BaseModel):
    question: str
    entities: List[Dict[str, Any]]
    relationships: List[GraphEdge]
    facts: List[CompressedDocument]
    sources: List[str]

class EvidencePackageBuilder:
    @staticmethod
    def calculate_token_surrogate(text: str) -> int:
        """Surrogate token counter mapping 4 characters to 1 token."""
        return len(text) // 4

    def assemble_package(self, question: str, seed_ids: List[str], graph_edges: List[GraphEdge], compressed_docs: List[CompressedDocument], all_entities: List[Dict[str, Any]]) -> EvidencePackage:
        allocated_entities: List[Dict[str, Any]] = []
        allocated_edges: List[GraphEdge] = []
        allocated_facts: List[CompressedDocument] = []
        allocated_sources: List[str] = []
        
        accumulated_tokens = EvidencePackageBuilder.calculate_token_surrogate(question)
        target_ids = set(seed_ids)

        # 1. Budget and attach structural core entities
        for ent in all_entities:
            if ent["id"] in target_ids:
                serialized_ent = f"{ent['id']}-{ent['name']}-{ent['type']}"
                tokens = EvidencePackageBuilder.calculate_token_surrogate(serialized_ent)
                if accumulated_tokens + tokens < settings.CONTEXT_TOKEN_BUDGET:
                    allocated_entities.append(ent)
                    accumulated_tokens += tokens

        # 2. Budget and attach topological graph edges
        for edge in graph_edges:
            serialized_edge = f"{edge.source}-{edge.target}-{edge.context}"
            tokens = EvidencePackageBuilder.calculate_token_surrogate(serialized_edge)
            if accumulated_tokens + tokens < settings.CONTEXT_TOKEN_BUDGET:
                allocated_edges.append(edge)
                accumulated_tokens += tokens

        # 3. Budget and attach dense compressed intelligence abstracts
        for c_doc in compressed_docs:
            serialized_fact = f"{c_doc.entity} {c_doc.summary} {' '.join(c_doc.key_facts)}"
            tokens = EvidencePackageBuilder.calculate_token_surrogate(serialized_fact)
            if accumulated_tokens + tokens < settings.CONTEXT_TOKEN_BUDGET:
                allocated_facts.append(c_doc)
                accumulated_tokens += tokens
                
        # Link source file path indices
        for ent in allocated_entities:
            if "path" in ent and ent["path"] not in allocated_sources:
                allocated_sources.append(ent["path"])

        return EvidencePackage(
            question=question,
            entities=allocated_entities,
            relationships=allocated_edges,
            facts=allocated_facts,
            sources=allocated_sources
        )