# atis/retrieval/retrieval_engine.py
import json
import logging
import re
import math
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
from pathlib import Path

from atis.config import settings 

logger = logging.getLogger("atis.retrieval")

class GraphCandidate(dict):
    def __init__(self, entity: Dict[str, Any], relationships: List[Dict[str, Any]]):
        super().__init__(entity=entity, relationships=relationships)

    def __getattr__(self, name: str) -> Any:
        if name == "entity_name": return self["entity"].get("name", "")
        if name == "entity_id": return self["entity"].get("id", "")
        if name == "entity_type": return self["entity"].get("type", "")
        if name in self: return self[name]
        if "entity" in self: return self["entity"].get(name, "")
        raise AttributeError(f"'GraphCandidate' object has no attribute '{name}'")

ExtractedCandidate = GraphCandidate

class RetrievalEngine:
    def __init__(self):
        logger.info("Initializing Schema-Aware Semantic Graph Engine...")
        self.entities_path: Path = settings.ENTITIES_JSON
        self.relationships_path: Path = settings.RELATIONSHIPS_JSON
        
        self._entity_registry = {}
        self._token_index = defaultdict(set)
        self._is_indexed = False
        self._node_degrees = defaultdict(int)
        
        self._semantic_graph = {
            "location": defaultdict(list),   
            "ownership_out": defaultdict(list),  
            "ownership_in": defaultdict(list),   
            "regulation": defaultdict(list), 
            "generic": defaultdict(list)     
        }
        
        self.regex_location = re.compile(r'location\s*:', re.IGNORECASE)
        self.regex_ownership = re.compile(r'owned\s*by\s*:', re.IGNORECASE)
        self.regex_regulation = re.compile(r'(regulated\s*by|licensing\s*authority|government\s*entities)\s*:', re.IGNORECASE)

    def _normalize_token(self, val: Any) -> str:
        if not val: return ""
        s = str(val).lower().strip()
        if "\\" in s or "/" in s: s = s.split("\\")[-1].split("/")[-1]
        if s.endswith(".md"): s = s[:-3]
        return s.replace("_", " ").replace("-", " ").strip()

    def _get_token_set(self, text: str) -> Set[str]:
        return set(re.findall(r'\b\w+\b', self._normalize_token(text)))

    def _build_semantic_indexes(self):
        if self._is_indexed: return
        
        logger.info("Deconstructing schema relationship markdown contexts...")
        try:
            with open(self.entities_path, "r", encoding="utf-8") as f:
                entities_data = json.load(f)
            with open(self.relationships_path, "r", encoding="utf-8") as f:
                relationships_data = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Unable to load graph data: {e}")

        excluded_fields = {"raw_content", "html", "full_text"}
        
        for ent in entities_data:
            ent_id = self._normalize_token(ent.get("id") or ent.get("name"))
            if not ent_id: continue
            
            clean_ent = {k: v for k, v in ent.items() if k not in excluded_fields}
            
            for k, v in clean_ent.items():
                if isinstance(v, str) and len(v) > 600:
                    clean_ent[k] = v[:600] + "... [TRUNCATED]"
                    
            self._entity_registry[ent_id] = clean_ent
            
            # UPGRADE: Deep Property Token Indexing (Scrapes text attributes for keywords)
            tokens = self._get_token_set(ent_id)
            if ent.get("name"):
                tokens.update(self._get_token_set(ent.get("name")))
            for k, v in clean_ent.items():
                if isinstance(v, str):
                    tokens.update(self._get_token_set(v))
                
            for token in tokens:
                if len(token) > 2:  
                    self._token_index[token].add(ent_id)

        for rel in relationships_data:
            src = self._normalize_token(rel.get("source"))
            tgt = self._normalize_token(rel.get("target"))
            context_str = str(rel.get("context", "")).lower()
            
            if not src or not tgt: continue
            
            self._node_degrees[src] += 1
            self._node_degrees[tgt] += 1
            
            if self.regex_location.search(context_str):
                self._semantic_graph["location"][src].append((tgt, rel))
                self._semantic_graph["location"][tgt].append((src, rel))
            elif self.regex_ownership.search(context_str):
                self._semantic_graph["ownership_out"][src].append((tgt, rel))
                self._semantic_graph["ownership_in"][tgt].append((src, rel))
            elif self.regex_regulation.search(context_str):
                self._semantic_graph["regulation"][src].append((tgt, rel))
                self._semantic_graph["regulation"][tgt].append((src, rel))
            else:
                self._semantic_graph["generic"][src].append((tgt, rel))
                self._semantic_graph["generic"][tgt].append((src, rel))
                
        self._is_indexed = True
        logger.info("Semantic adjacency optimization successfully built in memory.")

    def execute_hybrid_query(self, plan: Any) -> List[Dict[str, Any]]:
        self._build_semantic_indexes()
        
        raw_seeds = []

        for attr_name, value in vars(plan).items():

            if attr_name in {"query", "intent", "question"}:
                continue

            if isinstance(value, list):
                raw_seeds.extend(
                    v.strip()
                    for v in value
                    if isinstance(v, str) and v.strip()
                )

            elif isinstance(value, str) and value.strip():
                raw_seeds.append(value.strip())

        raw_seeds = list(set(raw_seeds))

        if getattr(plan, "query", None):
            raw_seeds.append(plan.query.strip())
                
        if getattr(plan, "query", None):
            raw_seeds.append(plan.query)
            
        logger.info(f"Executing Multi-Entry Graph Path Execution for Seeds: {raw_seeds}")
        if not raw_seeds: return []
            
        # Extract unique query tokens across all seeds for traversal metrics
        query_tokens = set()
        for seed in raw_seeds:
            query_tokens.update(self._get_token_set(seed))

        # ---------------------------------------------------------------------
        # SEED RESOLUTION PHASE: Soft Overlap Anchor Allocation
        # ---------------------------------------------------------------------
        resolved_anchor_nodes = set()
        for seed in raw_seeds:
            seed_tokens = self._get_token_set(seed)
            if not seed_tokens: continue
            
            for token in seed_tokens:
                matches = self._token_index.get(token, set())
                resolved_anchor_nodes.update(matches)

        logger.info(f"Resolved natural seeds to structural graph anchors: {list(resolved_anchor_nodes)}")
        if not resolved_anchor_nodes:
            return []

        # ---------------------------------------------------------------------
        # O(2) NEIGHBORHOOD TRAVERSAL: Score-Guided Fanout Sorting
        # ---------------------------------------------------------------------
        MAX_HOP_FANOUT = 50
        seen_edge_keys = set()
        provenance_edges = []
        
        def _process_edges(node: str, channels: List[str], target_tokens: Set[str]) -> List[Tuple[str, str]]:
            candidate_edges = []
            for channel in channels:
                edges = self._semantic_graph[channel].get(node, [])
                for neighbor, edge in edges:
                    # Calculate relevance of the relationship context to the overall query strings
                    edge_ctx = str(edge.get("context", "")).lower()
                    edge_tokens = self._get_token_set(edge_ctx)
                    neighbor_tokens = self._get_token_set(neighbor)
                    
                    # Score based on how many target terms are hit by this specific connection
                    overlap_score = len(target_tokens.intersection(edge_tokens | neighbor_tokens))
                    candidate_edges.append((neighbor, channel, edge, overlap_score))
            
            # UPGRADE: Sort connections by target query relevance BEFORE truncating super-nodes
            candidate_edges.sort(key=lambda x: x[3], reverse=True)
            
            neighbors = []
            for neighbor, channel, edge, _ in candidate_edges[:MAX_HOP_FANOUT]:
                edge_key = (self._normalize_token(edge.get("source")), self._normalize_token(edge.get("target")), channel)
                if edge_key not in seen_edge_keys:
                    seen_edge_keys.add(edge_key)
                    edge["channel"] = channel
                    provenance_edges.append(edge)
                neighbors.append((neighbor, channel))
            return neighbors

        # Hop 1 Execution
        hop_1_nodes = {} 
        all_channels = list(self._semantic_graph.keys())
        for anchor in resolved_anchor_nodes:
            for neighbor, channel in _process_edges(anchor, all_channels, query_tokens):
                hop_1_nodes[neighbor] = channel

        # Hop 2 Execution
        hop_2_nodes = {}
        for middle_node in hop_1_nodes.keys():
            if middle_node in resolved_anchor_nodes: continue
            for neighbor, channel in _process_edges(middle_node, all_channels, query_tokens):
                if neighbor not in resolved_anchor_nodes and neighbor not in hop_1_nodes:
                    hop_2_nodes[neighbor] = channel

        # ---------------------------------------------------------------------
        # DYNAMIC WEIGHTING & ALGEBRAIC RE-RANKING
        # ---------------------------------------------------------------------
        CHANNEL_WEIGHTS = {
            "ownership_out": 40,
            "ownership_in": 30,
            "regulation": 25,
            "location": 20,
            "generic": 5
        }
        
        tracked_network_nodes = resolved_anchor_nodes | set(hop_1_nodes.keys()) | set(hop_2_nodes.keys())
        candidates = []
        
        for node_id in tracked_network_nodes:
            if node_id not in self._entity_registry: continue
            
            entity = self._entity_registry[node_id].copy()
            filtered_links = [
                r for r in provenance_edges 
                if self._normalize_token(r.get("source")) == node_id or self._normalize_token(r.get("target")) == node_id
            ]
            
            score = 0
            
            # 1. Path Structural Proximity
            if node_id in resolved_anchor_nodes: score += 100
            elif node_id in hop_1_nodes: score += 60
            elif node_id in hop_2_nodes: score += 25
            
            # 2. Channel Priority Integration
            if node_id in hop_1_nodes:
                score += CHANNEL_WEIGHTS.get(hop_1_nodes[node_id], 0)
            elif node_id in hop_2_nodes:
                score += CHANNEL_WEIGHTS.get(hop_2_nodes[node_id], 0)
                
            # 3. Structural Link Density
            score += len(filtered_links) * 3
            
            # 4. Logarithmic Super-Node Degree Penalty
            degree = self._node_degrees.get(node_id, 0)
            degree_penalty = math.log(degree + 1) * 12
            score -= degree_penalty
            
            # 5. UPGRADE: Direct Content Token Overlap Bonus 
            node_text_tokens = self._get_token_set(node_id)
            for k, v in entity.items():
                if isinstance(v, str):
                    node_text_tokens.update(self._get_token_set(v))
            token_hits = len(query_tokens.intersection(node_text_tokens))
            score += token_hits * 20

            # INTENT-AWARE ENTITY BOOSTING
            person_indicators = {"person", "individual", "individuals", "names", "name", "who", "directory", "centric", "positions"}
            is_person = entity.get("type", "").lower() == "person"
            
            if query_tokens.intersection(person_indicators) and is_person:
                score += 150  # Dynamic structural floor elevation
                
                # --- NEW LOGICAL FIX: Role Adjacency Boost ---
                # If this person is directly linked to a mining or ministerial role, elevate them further
                for edge in filtered_links:
                    edge_context = str(edge.get("context", "")).lower()
                    if "minister" in edge_context or "mining" in edge_context or "secretary" in edge_context:
                        score += 100
                        break

            gc = GraphCandidate(entity=entity, relationships=filtered_links)
            gc["relevance_score"] = max(0, score)
            candidates.append(gc)

        # Sort and expand pool to 15 to ensure total leadership coverage
        candidates.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return candidates[:15]