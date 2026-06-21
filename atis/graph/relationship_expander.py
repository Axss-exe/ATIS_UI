import json
from pathlib import Path
from typing import List, Dict, Any, Set
from pydantic import BaseModel
from config import settings

class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str
    context: str

class RelationshipExpander:
    def __init__(self, relationships_path: Path = settings.RELATIONSHIPS_JSON):
        with open(relationships_path, "r", encoding="utf-8") as f:
            self.relationships: List[Dict[str, Any]] = json.load(f)

    def expand_subgraph(self, root_entity_ids: List[str], max_depth: int = settings.MAX_RELATIONSHIP_DEPTH) -> List[GraphEdge]:
        discovered_edges: List[GraphEdge] = []
        processed_edges_signatures: Set[str] = set()
        active_frontier: Set[str] = set(root_entity_ids)
        visited_nodes: Set[str] = set()

        for current_depth in range(max_depth):
            if not active_frontier:
                break
            
            next_frontier: Set[str] = set()
            for entity_id in active_frontier:
                if entity_id in visited_nodes:
                    continue
                visited_nodes.add(entity_id)

                for rel in self.relationships:
                    src = rel["source"]
                    tgt = rel["target"]
                    
                    if src == entity_id or tgt == entity_id:
                        edge_sig = f"{src}::{tgt}::{rel.get('context','')}"
                        if edge_sig not in processed_edges_signatures:
                            processed_edges_signatures.add(edge_sig)
                            edge_obj = GraphEdge(
                                source=src,
                                target=tgt,
                                relationship=rel.get("relationship", "wikilink_reference"),
                                context=rel.get("context", "")
                            )
                            discovered_edges.append(edge_obj)
                            
                            # Append unvisited node to the next frontier loop
                            neighbor = tgt if src == entity_id else src
                            if neighbor not in visited_nodes:
                                next_frontier.add(neighbor)
                                
            active_frontier = next_frontier

        return discovered_edges