# atis/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class ATISSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ATIS_", env_file=".env", extra="ignore")
    
    # Storage Infrastructure Paths (pointing one level up to project root data)
    DATA_DIR: Path = Path("../data")
    DOCUMENTS_JSON: Path = Path("data/documents.json")
    ENTITIES_JSON: Path = Path("data/entities.json")
    RELATIONSHIPS_JSON: Path = Path("data/relationships.json")
    SEARCH_INDEX_JSON: Path = Path("data/search_index.json")
    
    # Cerebras Infrastructure Configuration
    LLM_API_KEY: str
    LLM_BASE_URL: str = "https://api.cerebras.ai/v1"
    LLM_MODEL: str = "gpt-oss-120b"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_RETRIES: int = 3
    
    # Runtime Retrieval Hyperparameters
    FUZZY_MATCH_THRESHOLD: float = 0.60
    ENTITY_SCORE_WEIGHT_EXACT: float = 0.50
    ENTITY_SCORE_WEIGHT_TOKEN: float = 0.50
    MAX_RELATIONSHIP_DEPTH: int = 2
    CONTEXT_TOKEN_BUDGET: int = 12000

settings = ATISSettings()