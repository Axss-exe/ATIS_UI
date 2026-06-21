# atis/orchestrator/compiler_orchestrator.py
import logging
from typing import Dict, Any

from atis.planner.query_planner import QueryPlanner
from atis.retrieval.retrieval_engine import RetrievalEngine
from atis.context.context_builder import ContextBuilder
from atis.reasoning.reasoning_engine import ReasoningEngine

logger = logging.getLogger("atis.orchestrator")

class AtisCompilerOrchestrator:
    def __init__(self):
        logger.info("Initializing ATIS Compiler Core...")
        self.planner = QueryPlanner()
        self.retrieval_engine = RetrievalEngine()
        self.context_builder = ContextBuilder()
        self.reasoning_engine = ReasoningEngine()

    def compile(self, intelligence_requirement: str) -> Dict[str, Any]:
        logger.info(f"Processing target requirement: '{intelligence_requirement}'")
        
        # Phase 1: Planning
        plan = self.planner.generate_plan(intelligence_requirement)
        
        # Phase 2: Hybrid Retrieval
        candidates = self.retrieval_engine.execute_hybrid_query(plan)
        
        # Phase 3: Context Stacking & Reasoning Frame
        structured_context = self.context_builder.build_context_window(candidates)
        final_report = self.reasoning_engine.synthesize_final_response(
            intelligence_requirement, structured_context
        )
        
        return {
            "plan": plan.model_dump(),
            "candidate_count": len(candidates),
            "report": final_report
        }