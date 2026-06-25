# atis/orchestrator/compiler_orchestrator.py
import logging
import time  # COMPONENT ADDITION: Built-in time module for rate-limiting
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
        
        # Phase 1: Planning (Triggers LLM Request #1)
        plan = self.planner.generate_plan(intelligence_requirement)
        
        # RATE LIMIT GUARD: Space out the planning phase from the heavy retrieval framework
        logger.info("Enforcing rate-limit cooling period after planning phase...")
        time.sleep(12)
        
        # Phase 2: Hybrid Retrieval (Local Graph Memory Optimization)
        candidates = self.retrieval_engine.execute_hybrid_query(plan)
        
        # Phase 3: Context Stacking & Reasoning Frame (Triggers Heavy Context LLM Request #2)
        structured_context = self.context_builder.build_context_window(candidates)
        final_report = self.reasoning_engine.synthesize_final_response(
            intelligence_requirement, structured_context
        )
        
        # RATE LIMIT GUARD: Protect the sliding 5 requests/minute window before finishing the frame
        logger.info("Enforcing post-synthesis rate-limit cooling period...")
        time.sleep(12)
        
        # Phase 4: Construct the V0 Frontend JSON Package
        logger.info("Mapping graph attributes to structural V0 JSON payload...")
        
        v0_nodes = []
        v0_edges = []
        seen_edges = set()
        
        for cand in candidates:
            ent = cand.get("entity", {})
            if ent:
                node_id = ent.get("id")
                if node_id:
                    v0_nodes.append({
                        "id": node_id,
                        "label": ent.get("name", node_id),
                        "type": ent.get("type", "entity").lower(),
                        "metadata": {k: v for k, v in ent.items() if k not in ["id", "name", "type"]}
                    })
            
            for edge in cand.get("relationships", []):
                src = edge.get("source")
                tgt = edge.get("target")
                edge_type = edge.get("channel", "connected_to")
                edge_key = f"{src}-{edge_type}-{tgt}"
                
                if edge_key not in seen_edges:
                    v0_edges.append({
                        "source": src,
                        "target": tgt,
                        "type": edge_type,
                        "evidence": edge.get("context", "")
                    })
                    seen_edges.add(edge_key)

        # Defensive Extractor Hook: Uses a structured extraction method if defined on the engine
        if hasattr(self.reasoning_engine, "extract_structured_cards"):
            dashboard_cards = self.reasoning_engine.extract_structured_cards(
                intelligence_requirement, final_report
            )
            logger.info("Enforcing rate-limit cooling period after secondary extraction call...")
            time.sleep(12)
        else:
            dashboard_cards = {}

        v0_json_data = {
            "query": intelligence_requirement,
            "summary": dashboard_cards.get("summary", []),
            "entities": v0_nodes,
            "relationships": v0_edges,
            "opportunities": dashboard_cards.get("opportunities", []),
            "risks": dashboard_cards.get("risks", []),
            "recommendations": dashboard_cards.get("recommendations", []),
            "tables": dashboard_cards.get("tables", []),
            "raw_report": final_report
        }
        
        return {
            "plan": plan.model_dump(),
            "candidate_count": len(candidates),
            "report": final_report,
            "v0_json": v0_json_data
        }