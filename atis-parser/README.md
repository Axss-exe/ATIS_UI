# ATIS Knowledge Base Parser Engine

Production-grade pipeline utility to process unstructured Obsidian Knowledge Base structures into relational semantic matrices to power Search Indexes, Knowledge Graphs, and Retrieval-Augmented Generation (RAG) frameworks.

## Pipeline Architecture Processing

[ Obsidian Vault ] ──> (First Pass: Indexing & ID Creation) 
│ 
├──> (Second Pass: Extraction & Inference) 
│
├──> /data/documents.json 
├──> /data/entities.json 
├──> /data/relationships.json 
└──> /data/search_index.json

### System Processing Specifications

1. **Fallback Resolution Hierarchy**: Context mapping prioritizes explicit YAML keys (`entity_type`, `id`, `country`), falling back gracefully to relative folder path mappings and localized file semantics if unassigned. 
2. **Relationship Graph Strategy**: Captures localized sentence/header boundaries wrapping external Wikilink structures (`[[Target]]`) to supply upstream components with context window primitives. 
3. **Idempotence**: Node ID creation uses path and name sanitization tokens. Duplicate file names throughout separate country partitions resolve safely via structural content hashing allocations. 

## Installation & Requirements

Ensure standard Python 3.8+ dependencies are met: 

```bash

pip install PyYAML