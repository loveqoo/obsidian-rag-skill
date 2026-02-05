---
name: obsidian-rag
description: Semantic search for Git-based Obsidian Vaults. Provides full indexing, incremental updates, and search capabilities.
setup: ./scripts/setup.sh
---

# Obsidian RAG Skill

A RAG (Retrieval-Augmented Generation) skill for Obsidian Vaults based on Git repositories.

## Requirements
- Python 3.9-3.12
- Git repository

## Installation
Setup runs automatically when the skill is first invoked. It handles:
- Python 3.9~3.12 detection (auto-installs via pyenv if needed)
- Virtual environment creation and dependency installation
- `.gitignore` configuration (`chroma_db/`, `.venv/`)
- Git hook installation (`pre-push`, `post-merge`)

To run manually:
```bash
./scripts/setup.sh
```

## Usage

All commands use the venv Python directly:
```bash
.venv/bin/python scripts/obsidian_rag.py full-index              # Full indexing
.venv/bin/python scripts/obsidian_rag.py incremental-update       # Incremental update
.venv/bin/python scripts/obsidian_rag.py search --query "term"    # Search
.venv/bin/python scripts/obsidian_rag.py stats                    # Statistics
.venv/bin/python scripts/obsidian_rag.py test                     # Test
```

## Git Hooks (auto-installed)
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
