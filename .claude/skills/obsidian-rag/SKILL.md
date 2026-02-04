---
name: obsidian-rag
description: Semantic search for Git-based Obsidian Vaults. Provides full indexing, incremental updates, and search capabilities.
---

# Obsidian RAG Skill

A RAG (Retrieval-Augmented Generation) skill for Obsidian Vaults based on Git repositories.

## Requirements
- Python 3.9-3.12
- Git repository

## Installation
```bash
cd .claude/skills/obsidian-rag/scripts
./setup.sh
```

## Usage

### Full Indexing
Index all markdown files in the vault.
```bash
python scripts/obsidian_rag.py full-index
```

### Incremental Update
Update only files changed since the last indexing.
```bash
python scripts/obsidian_rag.py incremental-update
```

### Search
Perform semantic search and return results in JSON format.
```bash
python scripts/obsidian_rag.py search --query "search term" --top-k 5
```

### Statistics
View index statistics.
```bash
python scripts/obsidian_rag.py stats
```

### Test
Run tests to verify functionality.
```bash
python scripts/obsidian_rag.py test           # Basic execution
python scripts/obsidian_rag.py test -v        # Verbose output
python scripts/obsidian_rag.py test -k "parser"  # Run specific pattern tests only
```

## Git Hook Installation
Install Git hooks to automatically update the index on push/pull.
```bash
./scripts/install_hook.sh
```

Installed hooks:
- **pre-push**: Index changed markdown files before push
- **post-merge**: Index newly received markdown files after pull

## Uninstallation
Completely remove the skill and restore the original state.
```bash
./scripts/uninstall.sh
```

Items processed during uninstallation:
- `.gitignore` → Restore from `.gitignore_backup`
- Remove or restore Git hooks (pre-push, post-merge)
- Delete ChromaDB data
- Delete configuration files
- Delete skill folder (optional)

## Output Format
Search results are output in JSON format:
```json
{
  "query": "search term",
  "results": [
    {
      "file_path": "notes/example.md",
      "chunk_index": 0,
      "content": "Related content...",
      "distance": 0.234,
      "metadata": {
        "title": "Example Note",
        "tags": ["tag1", "tag2"]
      }
    }
  ],
  "total": 5
}
```
