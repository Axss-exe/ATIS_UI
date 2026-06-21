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
        Strips token-heavy JSON syntax and repetitive keys, converting
        the graph candidates into dense, readable Markdown.
        """
        lines = []
        for rank, cand in enumerate(candidates, 1):
            ent = cand.get("entity", {})
            name = ent.get("name", ent.get("id", "Unknown Node"))
            ent_type = ent.get("type", "Entity").upper()
            
            lines.append(f"### {rank}. {name} ({ent_type})")
            
            # 1. Add essential attributes (skip IDs and empty fields)
            for k, v in ent.items():
                if k not in ["id", "name", "type"] and v:
                    # Clean up random line breaks to save tokens
                    clean_val = str(v).replace('\n', ' ').strip()
                    lines.append(f"- {k.capitalize()}: {clean_val}")
                    
            # 2. Compress relationships to just the context strings
            rels = cand.get("relationships", [])
            if rels:
                lines.append("- Verified Connections:")
                seen_contexts = set()
                for r in rels:
                    ctx = r.get("context", "")
                    if ctx and ctx not in seen_contexts:
                        # Strip wikilink brackets [[ ]] as they waste tokens
                        clean_ctx = ctx.replace("[[", "").replace("]]", "").strip()
                        lines.append(f"  * {clean_ctx}")
                        seen_contexts.add(ctx)
            
            lines.append("") # Spacing
            
        return "\n".join(lines)