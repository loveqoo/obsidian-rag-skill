"""pytest 공통 fixture 정의."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_git_repo():
    """임시 Git 저장소를 생성하고 테스트 후 삭제한다."""
    temp_dir = tempfile.mkdtemp(prefix="obsidian_rag_test_")
    original_cwd = os.getcwd()

    try:
        os.chdir(temp_dir)
        subprocess.run(["git", "init"], capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            capture_output=True,
            check=True,
        )
        yield Path(temp_dir)
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_markdown_content():
    """테스트용 샘플 마크다운 콘텐츠를 반환한다."""
    return '''---
title: 테스트 노트
tags: [python, testing]
author: tester
---

# 테스트 노트

이것은 테스트용 노트입니다.

## 첫 번째 섹션

첫 번째 섹션의 내용입니다.
[[다른 노트]]에 대한 링크가 있습니다.

## 두 번째 섹션

두 번째 섹션의 내용입니다.
[[노트|별칭으로 표시]]와 같은 위키링크도 있습니다.

#inline-tag #another/nested
'''


@pytest.fixture
def sample_markdown_file(temp_git_repo, sample_markdown_content):
    """임시 Git 저장소에 샘플 마크다운 파일을 생성한다."""
    notes_dir = temp_git_repo / "notes"
    notes_dir.mkdir()

    file_path = notes_dir / "test_note.md"
    file_path.write_text(sample_markdown_content, encoding="utf-8")

    # Git에 커밋
    subprocess.run(["git", "add", "."], capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        capture_output=True,
        check=True,
    )

    return file_path


@pytest.fixture
def temp_chroma_db(temp_git_repo):
    """임시 ChromaDB 경로를 반환한다."""
    db_path = temp_git_repo / "chroma_db"
    db_path.mkdir()
    return db_path
