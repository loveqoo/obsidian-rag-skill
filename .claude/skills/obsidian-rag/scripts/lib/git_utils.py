"""Obsidian RAG용 Git 유틸리티."""

import subprocess
from pathlib import Path
from typing import Optional

from .config import get_project_root


def run_git_command(args: list[str], cwd: Optional[Path] = None) -> str:
    """Git 명령을 실행하고 출력을 반환한다."""
    cwd = cwd or get_project_root()
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_current_commit() -> str:
    """현재 HEAD 커밋 SHA를 반환한다."""
    return run_git_command(["rev-parse", "HEAD"])


def get_changed_files(
    since_commit: Optional[str] = None, file_pattern: str = "*.md"
) -> dict[str, list[str]]:
    """특정 커밋 이후 변경된 파일 목록을 반환한다.

    Args:
        since_commit: 비교 기준 커밋. None이면 모든 추적 파일 반환
        file_pattern: 파일 필터링 글롭 패턴

    Returns:
        'added', 'modified', 'deleted' 키를 가진 딕셔너리
    """
    project_root = get_project_root()

    if since_commit is None:
        # 모든 마크다운 파일 반환
        all_files = list(project_root.glob("**/*.md"))
        # 숨김 디렉토리와 chroma_db 제외
        valid_files = [
            str(f.relative_to(project_root))
            for f in all_files
            if not any(part.startswith(".") for part in f.parts)
            and "chroma_db" not in f.parts
        ]
        return {"added": valid_files, "modified": [], "deleted": []}

    try:
        # 상태와 함께 diff 가져오기
        output = run_git_command(
            ["diff", "--name-status", since_commit, "HEAD", "--", file_pattern]
        )
    except subprocess.CalledProcessError:
        # 커밋이 존재하지 않으면 모든 파일을 added로 반환
        return get_changed_files(since_commit=None, file_pattern=file_pattern)

    result: dict[str, list[str]] = {"added": [], "modified": [], "deleted": []}

    if not output:
        return result

    for line in output.split("\n"):
        if not line:
            continue

        parts = line.split("\t")
        if len(parts) < 2:
            continue

        status = parts[0][0]  # 상태의 첫 번째 문자
        file_path = parts[-1]  # 마지막 부분이 파일 경로 (이름 변경 처리)

        # 숨김 디렉토리와 chroma_db 제외
        if any(part.startswith(".") for part in Path(file_path).parts):
            continue
        if "chroma_db" in file_path:
            continue

        if status == "A":
            result["added"].append(file_path)
        elif status == "M":
            result["modified"].append(file_path)
        elif status == "D":
            result["deleted"].append(file_path)
        elif status == "R":
            # 이름 변경: 이전 경로는 deleted, 새 경로는 added
            if len(parts) >= 3:
                result["deleted"].append(parts[1])
                result["added"].append(parts[2])

    return result


def get_staged_files(file_pattern: str = "*.md") -> list[str]:
    """커밋을 위해 스테이징된 파일 목록을 반환한다.

    Args:
        file_pattern: 파일 필터링 글롭 패턴

    Returns:
        스테이징된 파일 경로 리스트
    """
    try:
        output = run_git_command(
            ["diff", "--cached", "--name-only", "--diff-filter=ACDMR", "--", file_pattern]
        )
    except subprocess.CalledProcessError:
        return []

    if not output:
        return []

    files = []
    for line in output.split("\n"):
        if line and not any(part.startswith(".") for part in Path(line).parts):
            files.append(line)

    return files


def is_git_repo(path: Optional[Path] = None) -> bool:
    """경로가 Git 저장소 내부인지 확인한다."""
    path = path or Path.cwd()
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path,
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False
