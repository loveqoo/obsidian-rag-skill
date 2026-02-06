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

Setup automatically creates `obsidian-rag` wrapper script in the project root directory.
All commands should be run from the **project root directory**:

```bash
./obsidian-rag full-index              # Full indexing
./obsidian-rag incremental-update       # Incremental update
./obsidian-rag search --query "term"    # Search
./obsidian-rag stats                    # Statistics
./obsidian-rag test                     # Test
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
