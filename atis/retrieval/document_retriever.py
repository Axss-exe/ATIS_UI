import json
from pathlib import Path
from typing import List, Dict, Any, Set
from pydantic import BaseModel
from config import settings
from graph.relationship_expander import GraphEdge

class TargetDocument(BaseModel):
    id: str
    name: str
    path: str
    country: str
    folder_classification: str
    metadata: Dict[str, Any]
    content: str
    relevance_score: float

class DocumentRetriever:
    def __init__(self, documents_path: Path = settings.DOCUMENTS_JSON):
        with open(documents_path, "r", encoding="utf-8") as f:
            self.documents: List[Dict[str, Any]] = json.load(f)

    def retrieve_documents(self, seed_ids: List[str], graph_edges: List[GraphEdge]) -> List[TargetDocument]:
        # Build the candidate node pool
        correlated_node_ids: Set[str] = set(seed_ids)
        for edge in graph_edges:
            correlated_node_ids.add(edge.source)
            correlated_node_ids.add(edge.target)

        matched_documents: List[TargetDocument] = []
        for doc in self.documents:
            doc_id = doc["id"]
            if doc_id in correlated_node_ids:
                # Prioritize seed documents over expanded graph nodes
                score = 1.0 if doc_id in seed_ids else 0.70
                
                matched_documents.append(TargetDocument(
                    id=doc_id,
                    name=doc["name"],
                    path=doc["path"],
                    country=doc["country"],
                    folder_classification=doc["folder_classification"],
                    metadata=doc.get("metadata", {}),
                    content=doc["content"],
                    relevance_score=score
                ))
                
        return sorted(matched_documents, key=lambda d: d.relevance_score, reverse=True)