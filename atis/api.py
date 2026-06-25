# atis/api.py
import sys
import json
from fastapi import FastAPI
from pydantic import BaseModel  # <-- FIXED: Pulled cleanly from pydantic
from atis.orchestrator.compiler_orchestrator import AtisCompilerOrchestrator

app = FastAPI(title="ATIS Frontend V0 Data Bridge")
orchestrator = AtisCompilerOrchestrator()

# Request body validation structure for web hooks
class QueryRequest(BaseModel):
    query: str

@app.post("/api/intelligence")
async def get_frontend_intel(payload: QueryRequest):
    """Web endpoint consumed by your V0 frontend hooks."""
    result = orchestrator.compile(payload.query)
    return result["v0_json"]


# ==============================================================================
# RUNTIME ENTRY ROUTER
# Allows you to run `python -m atis.api "query"` directly to inspect the JSON!
# ==============================================================================
if __name__ == "__main__":
    # If a query argument is passed via terminal: python -m atis.api "How is..."
    if len(sys.argv) > 1:
        cli_query = sys.argv[1]
        
        # Guard clause if you use this block to boot uvicorn manually later
        if cli_query not in ["server", "run"]:
            # Compile the single-source-of-truth payload
            execution_frame = orchestrator.compile(cli_query)
            
            # Print pristine, pretty-printed JSON directly to terminal console
            print(json.dumps(execution_frame["v0_json"], indent=2))
    else:
        # Fallback default: Boot up the local web server frame if run without arguments
        import uvicorn
        print("[INFO] Starting regional ATIS web infrastructure server...")
        uvicorn.run("atis.api:app", host="127.0.0.1", port=8000, reload=True)