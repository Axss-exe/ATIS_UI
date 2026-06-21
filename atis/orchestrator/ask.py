import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from config import settings
from planner.query_planner import QueryPlanner
from retrieval.entity_retriever import EntityRetriever
from graph.relationship_expander import RelationshipExpander
from retrieval.document_retriever import DocumentRetriever
from context.compressor import ContextCompressor
from context.evidence_builder import EvidencePackageBuilder
from reasoning.analyst import AnalystEngine, ATISReport

logger = logging.getLogger("atis.orchestrator")

class ATISAgent:
    def __init__(self):
        # Instantiate architectural components
        self.planner = QueryPlanner()
        self.entity_retriever = EntityRetriever()
        self.relationship_expander = RelationshipExpander()
        self.document_retriever = DocumentRetriever()
        self.compressor = ContextCompressor()
        self.evidence_builder = EvidencePackageBuilder()
        self.analyst = AnalystEngine()
        
        # Load global metadata baseline index
        with open(settings.ENTITIES_JSON, "r", encoding="utf-8") as f:
            self.global_entities: List[Dict[str, Any]] = json.load(f)

    def answer(self, question: str) -> ATISReport:
        logger.info(f"Initiating retrieval execution pipeline for question: '{question}'")
        
        # 1. Intent Mapping Optimization Phase
        plan = self.planner.generate_plan(question)
        
        # 2. Candidate Vector/Term Retrieval
        candidate_entities = self.entity_retriever.retrieve_candidates(plan)
        seed_ids = [ent.id for ent in candidate_entities]
        
        # 3. Relationship Graph Extension Passes
        graph_edges = self.relationship_expander.expand_subgraph(seed_ids)
        
        # 4. Context Document Materialization
        documents = self.document_retriever.retrieve_documents(seed_ids, graph_edges)
        
        # 5. Token-Safe Fact Compression Loops
        compressed_dossier = []
        for doc in documents:
            compressed_dossier.append(self.compressor.compress_document(doc))
            
        # 6. Compiling the Consolidated Evidence Package
        evidence_ d = self.evidence_builder.assemble_package(
            question=question,
            seed_ids=seed_ids,
            graph_edges=graph_edges,
            compressed_docs=compressed_dossier,
            all_entities=self.global_entities
        )
        
        # 7. Synthesizing the Analytical Report
        report = self.analyst.synthesize_report(evidence_d)
        return report