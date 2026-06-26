import sys
import json

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from atis.orchestrator.compiler_orchestrator import AtisCompilerOrchestrator


app = FastAPI(
    title="ATIS Frontend V0 Data Bridge"
)


# ==============================================================================
# DEBUG MIDDLEWARE
# ==============================================================================

@app.middleware("http")
async def add_debug_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-ATIS-DEBUG"] = "true"
    return response


# ==============================================================================
# CORS CONFIGURATION
# ==============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://vm-atis-frontend-build-68.vusercontent.net",
        "https://atis-ui-1.onrender.com",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# HEALTH + ROOT ROUTES
# Required for Render / deployment health checks
# ==============================================================================

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "ATIS Frontend V0 Data Bridge"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }



# ==============================================================================
# ATIS ORCHESTRATOR INITIALIZATION
# ==============================================================================

orchestrator = AtisCompilerOrchestrator()


# ==============================================================================
# REQUEST MODELS
# ==============================================================================

class QueryRequest(BaseModel):
    query: str


# ==============================================================================
# FRONTEND API ROUTES
# ==============================================================================

@app.post("/api/intelligence")
async def get_frontend_intel(payload: QueryRequest):
    """
    Web endpoint consumed by your V0 frontend hooks.
    
    Receives:
    {
        "query": "example intelligence question"
    }

    Returns:
    {
        ... v0_json payload ...
    }
    """

    result = orchestrator.compile(payload.query)

    return result["v0_json"]

# ==============================================================================
# V0 COMPATIBILITY ROUTE
# Supports frontend requests expecting /api/query
# ==============================================================================

@app.post("/api/query")
async def query_intelligence(payload: QueryRequest):
    """
    Compatibility endpoint for V0 frontend.
    
    Receives:
    {
        "query": "example intelligence question"
    }

    Returns:
    ATIS v0_json payload
    """

    result = orchestrator.compile(payload.query)

    return result["v0_json"]

# ==============================================================================
# CLI RUNTIME SUPPORT
#
# Allows:
#
# python -m atis.api "query"
#
# to directly test the compiler locally.
#
# ==============================================================================

if __name__ == "__main__":

    if len(sys.argv) > 1:

        cli_query = sys.argv[1]

        # Prevent accidental server boot commands
        if cli_query not in ["server", "run"]:

            execution_frame = orchestrator.compile(cli_query)

            print(
                json.dumps(
                    execution_frame["v0_json"],
                    indent=2
                )
            )

    else:

        import uvicorn

        print(
            "[INFO] Starting regional ATIS web infrastructure server..."
        )

        uvicorn.run(
            "atis.api:app",
            host="127.0.0.1",
            port=8000,
            reload=True
        )