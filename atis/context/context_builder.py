# atis/context/context_builder.py
import json
from typing import List, Any
from atis.retrieval.retrieval_engine import ExtractedCandidate

class ContextBuilder:
    def __init__(self):
        pass

    def build_context_window(self, candidates: List[ExtractedCandidate]) -> str:
        if not candidates:
            return "No matching records found in the intelligence retrieval space."
        
        # Route directly through the compression pipeline to stay within TPM quotas
        return self._compress_candidates_to_markdown(candidates)

    def _compress_candidates_to_markdown(self, candidates: List[ExtractedCandidate]) -> str:
        """
        Densely serializes up to 15 graph candidates. Employs ultra-strict 
        truncation on fields and limits total relationship edges to survive 
        within strict 30k TPM limits when processing major hub nodes.
        """
        lines = []
        for rank, cand in enumerate(candidates, 1):
            ent = cand.get("entity", {})
            name = ent.get("name", ent.get("id", "Unknown Node"))
            ent_type = ent.get("type", "Entity").upper()
            
            lines.append(f"### {rank}. {name} ({ent_type})")
            
            # Ultra-dense property values (90 chars max)
            for k, v in ent.items():
                if k not in ["id", "name", "type"] and v:
                    clean_val = str(v).replace('\n', ' ').strip()
                    if len(clean_val) > 90:
                        clean_val = clean_val[:87] + "..."
                    lines.append(f"- {k.capitalize()}: {clean_val}")
                    
            # Ultra-dense relationship contexts (90 chars max, max 6 edges per node)
            rels = cand.get("relationships", [])
            if rels:
                lines.append("- Verified Connections:")
                seen_relations = set()
                edge_count = 0
                
                # SLICE THE RELATIONS: Only process the first 6 unique structural edges
                for r in rels:
                    if edge_count >= 6:
                        break
                        
                    rel_type = r.get("channel", "connected_to").upper()
                    source = r.get("source", "").strip()
                    target = r.get("target", "").strip()
                    ctx = r.get("context", "")
                    
                    edge_key = f"{source} -> {rel_type} -> {target}"
                    
                    if edge_key not in seen_relations:
                        lines.append(f"  * [Edge]: {source.upper()} ({rel_type}) -> {target.upper()}")
                        if ctx:
                            clean_ctx = ctx.replace("[[", "").replace("]]", "").strip()
                            if len(clean_ctx) > 90:
                                clean_ctx = clean_ctx[:87] + "..."
                            lines.append(f"    [Context]: \"{clean_ctx}\"")
                        seen_relations.add(edge_key)
                        edge_count += 1
            
            lines.append("") 
            
        return "\n".join(lines)