#!/usr/bin/env python3
"""Obsidian RAG CLI - Semantic search for Git-based Obsidian Vaults."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Add lib path
sys.path.insert(0, str(Path(__file__).parent))

from lib.chunker import chunk_markdown_by_headers
from lib.chroma_manager import ChromaManager
from lib.config import (
    get_last_indexed_commit,
    get_project_root,
    get_vault_path,
    set_last_indexed_commit,
)
from lib.git_utils import get_changed_files, get_current_commit, is_git_repo


def cmd_full_index(args: argparse.Namespace) -> int:
    """Full indexing command - Index all markdown files."""
    if not is_git_repo():
        print(json.dumps({"error": "Not a Git repository"}))
        return 1

    vault_path = get_vault_path()
    manager = ChromaManager()

    # Delete existing data
    cleared = manager.clear()

    # Get all markdown files
    changes = get_changed_files(since_commit=None)
    all_files = changes["added"]

    total_chunks = 0
    indexed_files = []
    errors = []

    for file_path in all_files:
        full_path = vault_path / file_path
        if not full_path.exists():
            continue

        try:
            chunks = chunk_markdown_by_headers(full_path)
            if chunks:
                manager.add_chunks(chunks)
                total_chunks += len(chunks)
                indexed_files.append(file_path)
        except Exception as e:
            errors.append({"file": file_path, "error": str(e)})

    # Save current commit as last indexed commit
    try:
        current_commit = get_current_commit()
        set_last_indexed_commit(current_commit)
    except Exception:
        current_commit = None

    result = {
        "action": "full-index",
        "files_indexed": len(indexed_files),
        "chunks_created": total_chunks,
        "chunks_cleared": cleared,
        "last_commit": current_commit,
    }

    if errors:
        result["errors"] = errors

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_incremental_update(args: argparse.Namespace) -> int:
    """Incremental update command - Update only changed files."""
    if not is_git_repo():
        print(json.dumps({"error": "Not a Git repository"}))
        return 1

    vault_path = get_vault_path()
    manager = ChromaManager()
    last_commit = get_last_indexed_commit()

    if last_commit is None:
        # Run full indexing if no previous index exists
        print(
            json.dumps(
                {"message": "No previous index found. Running full indexing.", "action": "full-index"}
            )
        )
        return cmd_full_index(args)

    # Get changed files
    changes = get_changed_files(since_commit=last_commit)

    added_count = 0
    modified_count = 0
    deleted_count = 0
    chunks_added = 0
    chunks_deleted = 0
    errors = []

    # Process deleted files
    for file_path in changes["deleted"]:
        try:
            deleted = manager.delete_file(file_path)
            chunks_deleted += deleted
            deleted_count += 1
        except Exception as e:
            errors.append({"file": file_path, "error": str(e)})

    # Process added/modified files
    for file_path in changes["added"] + changes["modified"]:
        full_path = vault_path / file_path
        if not full_path.exists():
            continue

        try:
            chunks = chunk_markdown_by_headers(full_path)
            del_count, add_count = manager.update_file(file_path, chunks)
            chunks_deleted += del_count
            chunks_added += add_count

            if file_path in changes["added"]:
                added_count += 1
            else:
                modified_count += 1
        except Exception as e:
            errors.append({"file": file_path, "error": str(e)})

    # Update last indexed commit
    try:
        current_commit = get_current_commit()
        set_last_indexed_commit(current_commit)
    except Exception:
        current_commit = None

    result = {
        "action": "incremental-update",
        "files_added": added_count,
        "files_modified": modified_count,
        "files_deleted": deleted_count,
        "chunks_added": chunks_added,
        "chunks_deleted": chunks_deleted,
        "previous_commit": last_commit,
        "current_commit": current_commit,
    }

    if errors:
        result["errors"] = errors

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Search command - Perform semantic search in the vault."""
    if not is_git_repo():
        print(json.dumps({"error": "Not a Git repository"}))
        return 1

    manager = ChromaManager()

    # Check if index exists
    stats = manager.get_stats()
    if stats["total_chunks"] == 0:
        print(
            json.dumps(
                {
                    "error": "No index found. Please run 'full-index' first.",
                    "query": args.query,
                    "results": [],
                    "total": 0,
                }
            )
        )
        return 1

    results = manager.search(
        query=args.query, top_k=args.top_k, file_filter=args.file_filter
    )

    output = {
        "query": args.query,
        "results": results,
        "total": len(results),
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Stats command - Display index statistics."""
    if not is_git_repo():
        print(json.dumps({"error": "Not a Git repository"}))
        return 1

    manager = ChromaManager()
    stats = manager.get_stats()

    # Add last indexed commit
    stats["last_indexed_commit"] = get_last_indexed_commit()

    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Test command - Run tests with pytest."""
    script_dir = Path(__file__).parent
    tests_dir = script_dir / "tests"

    if not tests_dir.exists():
        print(json.dumps({"error": "Test directory not found", "path": str(tests_dir)}))
        return 1

    # Run pytest
    pytest_args = [sys.executable, "-m", "pytest", str(tests_dir)]

    if args.verbose:
        pytest_args.append("-v")

    if args.pattern:
        pytest_args.extend(["-k", args.pattern])

    if args.coverage:
        pytest_args.extend(["--cov=lib", "--cov-report=term-missing"])

    result = subprocess.run(pytest_args, cwd=script_dir)

    return result.returncode


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Obsidian RAG - Semantic search for Git-based Obsidian Vaults"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # full-index command
    parser_full = subparsers.add_parser(
        "full-index", help="Index all markdown files in the vault"
    )
    parser_full.set_defaults(func=cmd_full_index)

    # incremental-update command
    parser_incr = subparsers.add_parser(
        "incremental-update", help="Update files changed since last indexing"
    )
    parser_incr.set_defaults(func=cmd_incremental_update)

    # search command
    parser_search = subparsers.add_parser(
        "search", help="Search vault using semantic similarity"
    )
    parser_search.add_argument(
        "--query", "-q", required=True, help="Search query text"
    )
    parser_search.add_argument(
        "--top-k", "-k", type=int, default=5, help="Number of results to return (default: 5)"
    )
    parser_search.add_argument(
        "--file-filter", "-f", help="Filter results by file path prefix"
    )
    parser_search.set_defaults(func=cmd_search)

    # stats command
    parser_stats = subparsers.add_parser("stats", help="Show index statistics")
    parser_stats.set_defaults(func=cmd_stats)

    # test command
    parser_test = subparsers.add_parser("test", help="Run tests")
    parser_test.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    parser_test.add_argument(
        "-k", "--pattern", help="Run only tests matching the pattern"
    )
    parser_test.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser_test.set_defaults(func=cmd_test)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
