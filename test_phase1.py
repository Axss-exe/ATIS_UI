# test_phase1.py
import sys
import os
import json

# Force the root project directory into Python's search stack
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from atis.planner.query_planner import QueryPlanner

def run_test():
    print("=" * 60)
    print(" PHASE 1 INTEGRATION LIFT: CEREBRAS SYSTEM RUN")
    print("=" * 60)
    print("[*] Initializing gpt-oss-120b QueryPlanner...")
    
    try:
        planner = QueryPlanner()
        sample_query = "Which Chinese state-backed companies own lithium assets in Masvingo and who regulates them?"
        
        print(f"[*] Sending Intelligence Requirement:\n    \"{sample_query}\"\n")
        print("[*] Awaiting fast-inference optimization frame split...")
        
        plan = planner.generate_plan(sample_query)
        
        print("\n[✔] Retrieval Strategy Compiled Perfectly:")
        print("-" * 60)
        print(json.dumps(plan.model_dump(), indent=2))
        print("-" * 60)
        
    except Exception as e:
        print(f"\n[✗] Execution Fault: {str(e)}")

if __name__ == "__main__":
    run_test()