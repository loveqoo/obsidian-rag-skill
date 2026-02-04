"""통합 테스트."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCLIIntegration:
    """CLI 통합 테스트."""

    def test_전체_인덱싱(self, sample_markdown_file, temp_git_repo):
        """full-index 명령 테스트."""
        script_path = Path(__file__).parent.parent / "obsidian_rag.py"
        venv_python = Path(__file__).parent.parent.parent / ".venv" / "bin" / "python"

        # venv python이 없으면 시스템 python 사용
        python_cmd = str(venv_python) if venv_python.exists() else sys.executable

        result = subprocess.run(
            [python_cmd, str(script_path), "full-index"],
            capture_output=True,
            text=True,
            cwd=temp_git_repo,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["action"] == "full-index"
        assert output["files_indexed"] >= 1
        assert output["chunks_created"] >= 1

    def test_검색(self, sample_markdown_file, temp_git_repo):
        """search 명령 테스트."""
        script_path = Path(__file__).parent.parent / "obsidian_rag.py"
        venv_python = Path(__file__).parent.parent.parent / ".venv" / "bin" / "python"
        python_cmd = str(venv_python) if venv_python.exists() else sys.executable

        # 먼저 인덱싱
        subprocess.run(
            [python_cmd, str(script_path), "full-index"],
            capture_output=True,
            cwd=temp_git_repo,
        )

        # 검색 실행
        result = subprocess.run(
            [python_cmd, str(script_path), "search", "-q", "테스트"],
            capture_output=True,
            text=True,
            cwd=temp_git_repo,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "query" in output
        assert "results" in output
        assert output["query"] == "테스트"

    def test_증분_업데이트(self, sample_markdown_file, temp_git_repo):
        """incremental-update 명령 테스트."""
        script_path = Path(__file__).parent.parent / "obsidian_rag.py"
        venv_python = Path(__file__).parent.parent.parent / ".venv" / "bin" / "python"
        python_cmd = str(venv_python) if venv_python.exists() else sys.executable

        # 먼저 전체 인덱싱
        subprocess.run(
            [python_cmd, str(script_path), "full-index"],
            capture_output=True,
            cwd=temp_git_repo,
        )

        # 새 파일 추가
        new_file = temp_git_repo / "notes" / "new_note.md"
        new_file.write_text("""---
title: 새 노트
---

# 새 노트

새로운 내용입니다.
""", encoding="utf-8")

        subprocess.run(["git", "add", "."], capture_output=True, cwd=temp_git_repo)
        subprocess.run(
            ["git", "commit", "-m", "Add new note"],
            capture_output=True,
            cwd=temp_git_repo,
        )

        # 증분 업데이트 실행
        result = subprocess.run(
            [python_cmd, str(script_path), "incremental-update"],
            capture_output=True,
            text=True,
            cwd=temp_git_repo,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["action"] == "incremental-update"
        assert output["files_added"] >= 1

    def test_통계(self, sample_markdown_file, temp_git_repo):
        """stats 명령 테스트."""
        script_path = Path(__file__).parent.parent / "obsidian_rag.py"
        venv_python = Path(__file__).parent.parent.parent / ".venv" / "bin" / "python"
        python_cmd = str(venv_python) if venv_python.exists() else sys.executable

        # 먼저 인덱싱
        subprocess.run(
            [python_cmd, str(script_path), "full-index"],
            capture_output=True,
            cwd=temp_git_repo,
        )

        # 통계 조회
        result = subprocess.run(
            [python_cmd, str(script_path), "stats"],
            capture_output=True,
            text=True,
            cwd=temp_git_repo,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "total_chunks" in output
        assert output["total_chunks"] >= 1

    def test_Git_저장소_아닌_경우_오류(self, tmp_path):
        """Git 저장소가 아닌 경우 오류 테스트."""
        script_path = Path(__file__).parent.parent / "obsidian_rag.py"
        venv_python = Path(__file__).parent.parent.parent / ".venv" / "bin" / "python"
        python_cmd = str(venv_python) if venv_python.exists() else sys.executable

        result = subprocess.run(
            [python_cmd, str(script_path), "full-index"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert "error" in output
