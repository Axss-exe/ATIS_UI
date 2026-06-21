# test_phase2.py
import logging
import json
from atis.planner.query_planner import QueryPlanner
from atis.retrieval.retrieval_engine import RetrievalEngine

# Configure technical layout logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def run_phase2():
    print("=" * 60)
    print(" PHASE 2 INTEGRATION LIFT: HYBRID RETRIEVAL PIPELINE")
    print("=" * 60)
    
    # 1. Trigger Phase 1 Orchestration
    planner = QueryPlanner()
    question = "Which Chinese state-backed companies own lithium assets in Masvingo and who regulates them?"
    
    print(f"[*] Compiling Execution Strategy via Cerebras...")
    plan = planner.generate_plan(question)
    
    # 2. Route Strategy into Phase 2 Retrieval Engine
    retrieval_engine = RetrievalEngine()
    print(f"\n[*] Injecting RetrievalPlan payload into Hybrid Search Space...")
    results = retrieval_engine.execute_hybrid_query(plan)
    
    print(f"\n[✔] Retrieval Candidates Isolated ({len(results)} matches):")
    print("-" * 60)
    for idx, candidate in enumerate(results, 1):
        print(f"Candidate #{idx}: {candidate.entity_name} [{candidate.entity_type.upper()}]")
        print(f"  - Location: {candidate.location}")
        print(f"  - Vector Score: {candidate.confidence_score}")
        print(f"  - Isolated Relationships: {json.dumps(candidate.relationships)}")
        print(f"  - Snippet: {candidate.context_snippet}\n")
    print("-" * 60)

if __name__ == "__main__":
    run_phase2()