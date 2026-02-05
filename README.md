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

```bash
cd .claude/skills/obsidian-rag/scripts
./setup.sh
```

### 2. Full Indexing

Index all markdown files in the vault.

```bash
python .claude/skills/obsidian-rag/scripts/obsidian_rag.py full-index
```

### 3. Search

```bash
python .claude/skills/obsidian-rag/scripts/obsidian_rag.py search --query "search term" --top-k 5
```

### 4. Incremental Update

Update only changed files.

```bash
python .claude/skills/obsidian-rag/scripts/obsidian_rag.py incremental-update
```

## Commands

| Command | Description |
|---------|-------------|
| `full-index` | Index all markdown files |
| `incremental-update` | Update only changed files |
| `search --query "..." --top-k N` | Semantic search (default top-k: 5) |
| `stats` | Show index statistics |
| `test` | Run tests |

## Git Hook Installation

Install Git hooks for automatic index updates.

```bash
./scripts/install_hook.sh
```

Installed hooks:
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
python .claude/skills/obsidian-rag/scripts/obsidian_rag.py test

# Verbose output
python .claude/skills/obsidian-rag/scripts/obsidian_rag.py test -v

# Run specific pattern tests only
python .claude/skills/obsidian-rag/scripts/obsidian_rag.py test -k "parser"
```

## Uninstallation

```bash
./scripts/uninstall.sh
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
