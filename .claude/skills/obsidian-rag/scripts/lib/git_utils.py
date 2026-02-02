"""Git utilities for Obsidian RAG."""

import subprocess
from pathlib import Path
from typing import Optional

from .config import get_project_root


def run_git_command(args: list[str], cwd: Optional[Path] = None) -> str:
    """Run a git command and return output."""
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
    """Get the current HEAD commit SHA."""
    return run_git_command(["rev-parse", "HEAD"])


def get_changed_files(
    since_commit: Optional[str] = None, file_pattern: str = "*.md"
) -> dict[str, list[str]]:
    """Get files changed since a commit.

    Args:
        since_commit: The commit to compare against. If None, returns all tracked files.
        file_pattern: Glob pattern to filter files.

    Returns:
        Dictionary with keys 'added', 'modified', 'deleted' containing file paths.
    """
    project_root = get_project_root()

    if since_commit is None:
        # Return all markdown files
        all_files = list(project_root.glob("**/*.md"))
        # Filter out files in hidden directories and chroma_db
        valid_files = [
            str(f.relative_to(project_root))
            for f in all_files
            if not any(part.startswith(".") for part in f.parts)
            and "chroma_db" not in f.parts
        ]
        return {"added": valid_files, "modified": [], "deleted": []}

    try:
        # Get diff with status
        output = run_git_command(
            ["diff", "--name-status", since_commit, "HEAD", "--", file_pattern]
        )
    except subprocess.CalledProcessError:
        # If the commit doesn't exist, return all files as added
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

        status = parts[0][0]  # First character of status
        file_path = parts[-1]  # Last part is the file path (handles renames)

        # Filter out hidden directories and chroma_db
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
            # Rename: old path is deleted, new path is added
            if len(parts) >= 3:
                result["deleted"].append(parts[1])
                result["added"].append(parts[2])

    return result


def get_staged_files(file_pattern: str = "*.md") -> list[str]:
    """Get files staged for commit.

    Args:
        file_pattern: Glob pattern to filter files.

    Returns:
        List of staged file paths.
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
    """Check if the path is inside a git repository."""
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
