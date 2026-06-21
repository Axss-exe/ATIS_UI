# test_phase3.py
import logging
from atis.planner.query_planner import QueryPlanner
from atis.retrieval.retrieval_engine import RetrievalEngine
from atis.context.context_builder import ContextBuilder
from atis.reasoning.reasoning_engine import ReasoningEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
# Suppress noisy lower-level library logs for a clean output
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

def run_end_to_end():
    print("=" * 60)
    print(" ATIS COMPILER: END-TO-END SYSTEM RUN (PHASES 1 - 3)")
    print("=" * 60)
    
    question = "Which Chinese state-backed companies own lithium assets in Masvingo and who regulates them?"
    print(f"[*] Raw Intelligence Input: \"{question}\"\n")
    
    # Phase 1: Planning
    print("[*] Launching Phase 1: Query Planner...")
    planner = QueryPlanner()
    plan = planner.generate_plan(question)
    print("[✔] Strategy Compiled.")
    
    # Phase 2: Hybrid Retrieval
    print("\n[*] Launching Phase 2: Hybrid Retrieval Space Scan...")
    retrieval_engine = RetrievalEngine()
    candidates = retrieval_engine.execute_hybrid_query(plan)
    print(f"[✔] Retrieval Completed. Isolated {len(candidates)} candidate(s).")
    
    # Phase 3: Context Assembly & Synthesis
    print("\n[*] Launching Phase 3: Context Stacking & Reasoning Frame...")
    context_builder = ContextBuilder()
    structured_context = context_builder.build_context_window(candidates)
    
    reasoning_engine = ReasoningEngine()
    final_output = reasoning_engine.synthesize_final_response(question, structured_context)
    
    print("\n" + "=" * 60)
    print(" FINAL SYNTHESIZED INTELLIGENCE REPORT")
    print("=" * 60)
    print(final_output)
    print("=" * 60)

if __name__ == "__main__":
    run_end_to_end()