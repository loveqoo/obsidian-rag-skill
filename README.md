# Obsidian RAG Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

[한국어](README_ko.md)

A semantic search Claude Code skill for Git-based Obsidian Vaults. Uses ChromaDB and embeddings to index notes and enable natural language search.

## Key Features

- **Semantic Search**: Meaning-based search, not just keyword matching
- **Multilingual Support**: Uses `paraphrase-multilingual-MiniLM-L12-v2` embedding model (50+ languages including English, Korean, Japanese, Chinese, etc.)
- **Full Indexing**: Index all markdown files in the vault at once
- **Incremental Updates**: Selectively update only changed files
- **Git Hook Support**: Automatic index updates on push/pull
- **Obsidian Metadata Parsing**: Extracts YAML frontmatter, tags, and wikilinks

## Requirements

- Python 3.9-3.12
- Git repository

## Quick Start

### 1. Installation

Setup runs automatically when the skill is first invoked. It handles everything:
- Install Python 3.9-3.12 via pyenv (if needed)
- Create virtual environment and install dependencies
- Configure `.gitignore`
- Install Git hooks (`pre-push`, `post-merge`)
- Create `obsidian-rag` wrapper script in project root

### 2. Usage

All commands run from the **project root directory**:

```bash
# Full indexing
./obsidian-rag full-index

# Search
./obsidian-rag search --query "search term" --top-k 5

# Incremental update
./obsidian-rag incremental-update

# Statistics
./obsidian-rag stats
```

## Commands

| Command | Description |
|---------|-------------|
| `full-index` | Index all markdown files |
| `incremental-update` | Update only changed files |
| `search --query "..." --top-k N` | Semantic search (default top-k: 5) |
| `stats` | Show index statistics |
| `test` | Run tests |

## Git Hooks (auto-installed)

Git hooks are automatically installed during setup:
- **pre-push**: Index changed markdown files before push
- **post-merge**: Index newly received markdown files after pull

## Directory Structure

```
.claude/skills/obsidian-rag/
├── SKILL.md                 # Skill description file
└── scripts/
    ├── setup.sh             # Installation script
    ├── install_hook.sh      # Git hook installation
    ├── uninstall.sh         # Uninstall script
    ├── obsidian_rag.py      # Main CLI
    ├── requirements.txt     # Python dependencies
    ├── lib/                 # Core library
    │   ├── chroma_manager.py
    │   ├── chunker.py
    │   ├── config.py
    │   ├── git_utils.py
    │   └── obsidian_parser.py
    └── tests/               # Test files
```

## Running Tests

```bash
# Basic execution
./obsidian-rag test

# Verbose output
./obsidian-rag test -v

# Run specific pattern tests only
./obsidian-rag test -k "parser"
```

## Uninstallation

```bash
.claude/skills/obsidian-rag/scripts/uninstall.sh
```

## Search Result Format

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

## License

MIT License - See the [LICENSE](LICENSE) file for details.
