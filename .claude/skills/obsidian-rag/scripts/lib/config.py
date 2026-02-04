"""Obsidian RAG 설정 관리 모듈."""

import json
import os
from pathlib import Path
from typing import Optional

CONFIG_FILENAME = ".obsidian_rag_config.json"


def get_project_root() -> Path:
    """Git 저장소 루트 경로를 찾아 반환한다."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").is_dir():
            return current
        current = current.parent
    raise RuntimeError("Git 저장소 내부가 아닙니다")


def get_config_path() -> Path:
    """설정 파일 경로를 반환한다."""
    return get_project_root() / CONFIG_FILENAME


def get_chroma_db_path() -> Path:
    """ChromaDB 디렉토리 경로를 반환한다."""
    return get_project_root() / "chroma_db"


def load_config() -> dict:
    """설정 파일을 로드하여 반환한다."""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: dict) -> None:
    """설정을 파일에 저장한다."""
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_last_indexed_commit() -> Optional[str]:
    """마지막으로 인덱싱된 커밋 SHA를 반환한다."""
    config = load_config()
    return config.get("last_indexed_commit")


def set_last_indexed_commit(commit_sha: str) -> None:
    """마지막 인덱싱 커밋 SHA를 설정한다."""
    config = load_config()
    config["last_indexed_commit"] = commit_sha
    save_config(config)


def get_vault_path() -> Path:
    """Vault 경로를 반환한다 (기본값: 프로젝트 루트)."""
    config = load_config()
    vault_path = config.get("vault_path")
    if vault_path:
        return Path(vault_path)
    return get_project_root()
