import json
from pathlib import Path
from typing import List, Dict, Any, Set
from pydantic import BaseModel
from config import settings
from planner.query_planner import RetrievalPlan

class ScoredEntity(BaseModel):
    id: str
    score: float

class EntityRetriever:
    def __init__(self, entities_path: Path = settings.ENTITIES_JSON, search_index_path: Path = settings.SEARCH_INDEX_JSON):
        with open(entities_path, "r", encoding="utf-8") as f:
            self.entities: List[Dict[str, Any]] = json.load(f)
        with open(search_index_path, "r", encoding="utf-8") as f:
            self.search_index: List[Dict[str, Any]] = json.load(f)

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return EntityRetriever._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    @staticmethod
    def _fuzzy_score(s1: str, s2: str) -> float:
        s1, s2 = s1.lower().strip(), s2.lower().strip()
        if not s1 or not s2:
            return 0.0
        max_len = max(len(s1), len(s2))
        distance = EntityRetriever._levenshtein_distance(s1, s2)
        return 1.0 - (distance / max_len)

    def retrieve_candidates(self, plan: RetrievalPlan) -> List[ScoredEntity]:
        compiled_scores: Dict[str, float] = {}
        target_tokens: Set[str] = set()
        
        for q in plan.search_queries:
            target_tokens.update([t.lower() for t in q.split() if len(t) > 2])
        for t in plan.topics:
            target_tokens.add(t.lower())

        for idx_entry in self.search_index:
            entity_id = idx_entry["id"]
            entity_name = idx_entry["name"].lower()
            index_tokens = idx_entry.get("tokens", [])
            
            # Sub-score A: Direct Fuzzy Matching
            best_fuzzy = 0.0
            for query in plan.search_queries:
                f_score = self._fuzzy_score(query, entity_name)
                if f_score > best_fuzzy:
                    best_fuzzy = f_score
            
            # Sub-score B: Overlapping Search Tokens
            matched_tokens = [tok for tok in target_tokens if tok in index_tokens]
            token_score = len(matched_tokens) / len(target_tokens) if target_tokens else 0.0
            
            # Composite Scoring Formula
            final_score = (best_fuzzy * settings.ENTITY_SCORE_WEIGHT_EXACT) + (token_score * settings.ENTITY_SCORE_WEIGHT_TOKEN)
            
            # Filter matches by structural categories
            if plan.entity_types:
                ent_meta = next((e for e in self.entities if e["id"] == entity_id), None)
                if ent_meta and ent_meta.get("type") not in plan.entity_types:
                    final_score *= 0.5  # Soft degradation for type mismatches
                    
            if final_score >= settings.FUZZY_MATCH_THRESHOLD:
                compiled_scores[entity_id] = max(compiled_scores.get(entity_id, 0.0), round(final_score, 3))
                
        sorted_entities = sorted(compiled_scores.items(), key=lambda item: item[1], reverse=True)
        return [ScoredEntity(id=eid, score=scr) for eid, scr in sorted_entities]