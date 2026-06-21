#!/usr/bin/env python3
import os
import re
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set

# ==========================================
# SYSTEM CONFIGURATION
# ==========================================
VAULT_ROOT = Path("c:/Users/tmaki/Documents/workspace/atis-compiler")  # Change this path to your Obsidian Vault root
OUTPUT_DIR = Path("./data")
LOG_DIR = Path("./logs")

# Folder structural mappings to entity types
FOLDER_TYPE_MAP = {
    "companies": "company",
    "projects": "project",
    "people": "person",
    "regulatory agencies": "regulator",
    "regulators": "regulator",
    "legislation": "law",
    "ministries": "government ministry",
    "departments": "government department",
    "provinces": "region",
    "cities": "location",
    "mines": "company",
    "energy": "company",
    "environment": "company",
    "finance": "company",
    "schools": "company",
    "transport": "company"
}

# ==========================================
# UTILITY & ENGINE FUNCTIONS
# ==========================================

def slugify(text: str) -> str:
    """Generates clean, uniform strings suitable for stable IDs."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def generate_deterministic_id(name: str, relative_path: str, existing_ids: Set[str]) -> str:
    """
    Generates a human-readable deterministic ID.
    Appends path-based hash variations if collisions occur.
    """
    base_id = slugify(name)
    if not base_id:
        base_id = "unnamed-node"
        
    if base_id not in existing_ids:
        return base_id
        
    # Collision remediation using a hash slice of the file's unique path
    path_hash = hashlib.md5(relative_path.encode('utf-8')).hexdigest()[:6]
    collided_id = f"{base_id}-{path_hash}"
    return collided_id

def tokenize_text(text: str) -> List[str]:
    """Splits text into filtered lowercase structural elements for search indices."""
    tokens = re.findall(r'\b\w+\b', text.lower())
    return sorted(list(set([t for t in tokens if len(t) > 1])))

class ATISParser:
    def __init__(self, vault_path: Path, output_path: Path, log_path: Path):
        self.vault_path = vault_path.resolve()
        self.output_path = output_path
        self.log_path = log_path
        self.warnings: List[Dict[str, Any]] = []
        
        # In-memory tracking matrices
        self.documents: List[Dict[str, Any]] = []
        self.entities: List[Dict[str, Any]] = []
        self.relationships: List[Dict[str, Any]] = []
        self.search_index: List[Dict[str, Any]] = []
        
        # Fast lookup mapping: "Normalized Entity Name" -> "Generated system ID"
        self.name_to_id_map: Dict[str, str] = {}
        # Tracking set for generated unique IDs
        self.assigned_ids: Set[str] = set()

    def log_warning(self, file_path: str, message: str):
        """Appends parser issues to telemetry dataset without halting execution."""
        self.warnings.append({
            "file": file_path,
            "warning": message
        })

    def parse_frontmatter(self, content: str, rel_path: str) -> Tuple[Dict[str, Any], str]:
        """Separates YAML block from standard markdown body content safely."""
        frontmatter = {}
        body = content
        
        # Match standard Jekyll/Obsidian YAML blocks
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            raw_yaml = match.group(1)
            body = content[match.end():]
            try:
                frontmatter = yaml.safe_load(raw_yaml) or {}
            except yaml.YAMLError as e:
                self.log_warning(rel_path, f"Malformed YAML metadata frontmatter: {str(e)}")
                frontmatter = {}
        return frontmatter, body

    def infer_context(self, path: Path, metadata: Dict[str, Any]) -> Tuple[str, str, List[str]]:
        """
        Infers context leveraging structural design priorities:
        1. YAML Frontmatter -> 2. Deep Directory Hierarchy Mapping -> 3. Fallbacks
        """
        rel_parts = path.relative_to(self.vault_path).parts
        
        # 1. Infer Country (Accounting for the 'ATIS' root directory prefix)
        inferred_country = "Global"
        if len(rel_parts) > 1:
            if rel_parts[0].upper() == "ATIS" and len(rel_parts) > 2:
                inferred_country = rel_parts[1]  # Grab the actual country folder (e.g., China, Zimbabwe)
            else:
                inferred_country = rel_parts[0]  # Fallback if structure varies
            
        if "country" in metadata and metadata["country"]:
            inferred_country = metadata["country"]

        # 2. Infer Entity Type and category pathways
        inferred_type = "unknown"
        categories = []
        
        # Traverse backward up the folder tree parts to infer classification mapping
        for part in reversed(rel_parts[:-1]):
            clean_part = part.lower().strip()
            categories.append(clean_part)
            if clean_part in FOLDER_TYPE_MAP and inferred_type == "unknown":
                inferred_type = FOLDER_TYPE_MAP[clean_part]

        # Overwrite with precise metadata definitions if explicitly provided
        if "entity_type" in metadata and metadata["entity_type"]:
            inferred_type = metadata["entity_type"]
        elif inferred_type == "unknown":
            self.log_warning(str(path.relative_to(self.vault_path)), "Missing entity_type inferred from folder structure pathing.")

        return inferred_country, inferred_type, categories

    def extract_relationships(self, body_content: str, source_id: str, file_rel_path: str):
        """
        Parses context-aware Wikilinks. Extracts the precise contextual sentence or 
        neighboring line boundary to preserve relationships for processing.
        """
        lines = body_content.split('\n')
        for idx, line in enumerate(lines):
            # Matches standard patterns: [[TargetNode]] or [[TargetNode|Display Alias]]
            matches = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', line)
            for target_name in matches:
                target_name_clean = target_name.strip()
                target_id = self.name_to_id_map.get(target_name_clean.lower(), slugify(target_name_clean))
                
                # Context optimization strategy: Capture line or context prefix
                context = line.strip()
                if context == f"[[{target_name}]]" or context == f"[[{target_name_clean}]]":
                    # Look back one line if the current link line is isolated text
                    if idx > 0 and lines[idx-1].strip().endswith(':'):
                        context = f"{lines[idx-1].strip()} {context}"

                self.relationships.append({
                    "source": source_id,
                    "target": target_id,
                    "relationship": "wikilink_reference",
                    "context": context
                })

    def first_pass_scan(self):
        """Initial structural index walk over files to build reliable global name-to-ID indices."""
        for file_path in self.vault_path.rglob("*.md"):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(self.vault_path))
                name = file_path.stem
                
                # Read file raw to verify explicit IDs in YAML if existing
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        raw_content = f.read()
                except Exception as e:
                    self.log_warning(rel_path, f"Read access exception error: {str(e)}")
                    continue
                    
                meta, _ = self.parse_frontmatter(raw_content, rel_path)
                
                # Enforce identifier generation protocol
                if "id" in meta and meta["id"]:
                    doc_id = str(meta["id"])
                else:
                    doc_id = generate_deterministic_id(name, rel_path, self.assigned_ids)
                    if "id" not in meta:
                        self.log_warning(rel_path, f"Missing explicit UUID/UID. Auto-generated stable reference identity: '{doc_id}'")

                self.assigned_ids.add(doc_id)
                self.name_to_id_map[name.lower()] = doc_id
                
                # Map alternate syntax aliases if cataloged
                if "aliases" in meta and isinstance(meta["aliases"], list):
                    for alias in meta["aliases"]:
                        self.name_to_id_map[str(alias).lower()] = doc_id

    def second_pass_process(self):
        """Executes full operational content parsing, link mapping, and index compilation."""
        for file_path in self.vault_path.rglob("*.md"):
            if not file_path.is_file():
                continue
                
            rel_path = str(file_path.relative_to(self.vault_path))
            name = file_path.stem
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
            except Exception:
                continue # Warning logged in first pass
                
            meta, body = self.parse_frontmatter(raw_content, rel_path)
            doc_id = self.name_to_id_map.get(name.lower(), slugify(name))
            
            country, entity_type, categories = self.infer_context(file_path, meta)
            
            # Extract internal links
            wikilinks = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', body)
            wikilinks = sorted(list(set([l.strip() for l in wikilinks])))
            
            # Package document data object
            self.documents.append({
                "id": doc_id,
                "name": name,
                "path": rel_path,
                "country": country,
                "folder_classification": entity_type,
                "metadata": meta,
                "content": body.strip(),
                "links": wikilinks
            })
            
            # Package entity data object
            self.entities.append({
                "id": doc_id,
                "name": name,
                "type": entity_type,
                "country": country,
                "path": rel_path
            })
            
            # Package precise relationship mappings
            self.extract_relationships(body, doc_id, rel_path)
            
            # Construct tokens for keyphrase match engine
            aliases = meta.get("aliases", [])
            if not isinstance(aliases, list):
                aliases = [aliases]
                
            search_blob = f"{name} {' '.join([str(a) for a in aliases])} {entity_type} {' '.join(categories)} {country}"
            self.search_index.append({
                "id": doc_id,
                "name": name,
                "tokens": tokenize_text(search_blob),
                "folder_categories": categories
            })

    def serialize_outputs(self):
        """Writes compiled outputs securely to disk as formatted JSON datasets."""
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        io_matrix = [
            (self.output_path / "documents.json", self.documents),
            (self.output_path / "entities.json", self.entities),
            (self.output_path / "relationships.json", self.relationships),
            (self.output_path / "search_index.json", self.search_index),
            (self.log_path / "parser_warnings.json", self.warnings)
        ]
        
        for target_path, dataset in io_matrix:
            with open(target_path, 'w', encoding='utf-8') as dest:
                json.dump(dataset, dest, indent=2, ensure_ascii=False, default=str)
                
        print(f"[✔] Parse Pipeline Complete. Documents Processed: {len(self.documents)} | Warnings Raised: {len(self.warnings)}")

    def execute(self):
        """Runs pipeline stages sequentially."""
        if not self.vault_path.exists():
            print(f"[✘] Operational Failure: Target pipeline source directory path does not exist: {self.vault_path}")
            return
        self.first_pass_scan()
        self.second_pass_process()
        self.serialize_outputs()

if __name__ == "__main__":
    # Standard operational runtime execution
    parser_engine = ATISParser(
        vault_path=VAULT_ROOT,
        output_path=OUTPUT_DIR,
        log_path=LOG_DIR
    )
    parser_engine.execute()