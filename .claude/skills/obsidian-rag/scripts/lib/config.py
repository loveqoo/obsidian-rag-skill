"""Configuration management for Obsidian RAG."""

import json
import os
from pathlib import Path
from typing import Optional

CONFIG_FILENAME = ".obsidian_rag_config.json"


def get_project_root() -> Path:
    """Find the git repository root."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").is_dir():
            return current
        current = current.parent
    raise RuntimeError("Not inside a git repository")


def get_config_path() -> Path:
    """Get the path to the config file."""
    return get_project_root() / CONFIG_FILENAME


def get_chroma_db_path() -> Path:
    """Get the path to the ChromaDB directory."""
    return get_project_root() / "chroma_db"


def load_config() -> dict:
    """Load configuration from file."""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: dict) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_last_indexed_commit() -> Optional[str]:
    """Get the last indexed commit SHA."""
    config = load_config()
    return config.get("last_indexed_commit")


def set_last_indexed_commit(commit_sha: str) -> None:
    """Set the last indexed commit SHA."""
    config = load_config()
    config["last_indexed_commit"] = commit_sha
    save_config(config)


def get_vault_path() -> Path:
    """Get the vault path (project root by default)."""
    config = load_config()
    vault_path = config.get("vault_path")
    if vault_path:
        return Path(vault_path)
    return get_project_root()
