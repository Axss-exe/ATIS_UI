# atis/server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Import your working core modules
from atis.planner.query_planner import QueryPlanner
from atis.retrieval.retrieval_engine import RetrievalEngine
from atis.context.context_builder import ContextBuilder

# Initialize components
app = FastAPI(title="ATIS Intelligence Compiler API")
planner = QueryPlanner()
engine = RetrievalEngine()
context_builder = ContextBuilder()

# Enable CORS so your v0/Next.js frontend can talk to this API locally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, swap with your actual Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.post("/api/query")
async def handle_compile(payload: QueryRequest):
    try:
        # 1. Generate the upstream structured plan
        plan = planner.generate_plan(payload.question)
        
        # 2. Execute score-guided graph traversal
        candidates = engine.execute_hybrid_query(plan)
        
        # 3. Build the token-compressed markdown payload
        compiled_context = context_builder.build_context_window(candidates)
        
        return {
            "status": "success",
            "plan": plan.model_dump(),
            "context_markdown": compiled_context
        }
    except Exception as e:
        logging.error(f"API Execution Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))