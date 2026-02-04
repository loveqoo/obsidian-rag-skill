#!/usr/bin/env python3
"""Obsidian RAG CLI - Git 기반 옵시디언 Vault 시맨틱 검색."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# lib 경로 추가
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
    """전체 인덱싱 명령 - 모든 마크다운 파일을 인덱싱한다."""
    if not is_git_repo():
        print(json.dumps({"error": "Git 저장소가 아닙니다"}))
        return 1

    vault_path = get_vault_path()
    manager = ChromaManager()

    # 기존 데이터 삭제
    cleared = manager.clear()

    # 모든 마크다운 파일 가져오기
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

    # 현재 커밋을 마지막 인덱싱 커밋으로 저장
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
    """증분 업데이트 명령 - 변경된 파일만 업데이트한다."""
    if not is_git_repo():
        print(json.dumps({"error": "Git 저장소가 아닙니다"}))
        return 1

    vault_path = get_vault_path()
    manager = ChromaManager()
    last_commit = get_last_indexed_commit()

    if last_commit is None:
        # 이전 인덱스가 없으면 전체 인덱싱 실행
        print(
            json.dumps(
                {"message": "이전 인덱스가 없습니다. 전체 인덱싱을 실행합니다.", "action": "full-index"}
            )
        )
        return cmd_full_index(args)

    # 변경된 파일 가져오기
    changes = get_changed_files(since_commit=last_commit)

    added_count = 0
    modified_count = 0
    deleted_count = 0
    chunks_added = 0
    chunks_deleted = 0
    errors = []

    # 삭제된 파일 처리
    for file_path in changes["deleted"]:
        try:
            deleted = manager.delete_file(file_path)
            chunks_deleted += deleted
            deleted_count += 1
        except Exception as e:
            errors.append({"file": file_path, "error": str(e)})

    # 추가/수정된 파일 처리
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

    # 마지막 인덱싱 커밋 업데이트
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
    """검색 명령 - Vault에서 시맨틱 검색을 수행한다."""
    if not is_git_repo():
        print(json.dumps({"error": "Git 저장소가 아닙니다"}))
        return 1

    manager = ChromaManager()

    # 인덱스 존재 여부 확인
    stats = manager.get_stats()
    if stats["total_chunks"] == 0:
        print(
            json.dumps(
                {
                    "error": "인덱스가 없습니다. 먼저 'full-index'를 실행하세요.",
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
    """통계 명령 - 인덱스 통계를 표시한다."""
    if not is_git_repo():
        print(json.dumps({"error": "Git 저장소가 아닙니다"}))
        return 1

    manager = ChromaManager()
    stats = manager.get_stats()

    # 마지막 인덱싱 커밋 추가
    stats["last_indexed_commit"] = get_last_indexed_commit()

    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """테스트 명령 - pytest로 테스트를 실행한다."""
    script_dir = Path(__file__).parent
    tests_dir = script_dir / "tests"

    if not tests_dir.exists():
        print(json.dumps({"error": "테스트 디렉토리를 찾을 수 없습니다", "path": str(tests_dir)}))
        return 1

    # pytest 실행
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
    """메인 진입점."""
    parser = argparse.ArgumentParser(
        description="Obsidian RAG - Git 기반 옵시디언 Vault 시맨틱 검색"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # full-index 명령
    parser_full = subparsers.add_parser(
        "full-index", help="Vault의 모든 마크다운 파일 인덱싱"
    )
    parser_full.set_defaults(func=cmd_full_index)

    # incremental-update 명령
    parser_incr = subparsers.add_parser(
        "incremental-update", help="마지막 인덱싱 이후 변경된 파일 업데이트"
    )
    parser_incr.set_defaults(func=cmd_incremental_update)

    # search 명령
    parser_search = subparsers.add_parser(
        "search", help="시맨틱 유사도 기반 Vault 검색"
    )
    parser_search.add_argument(
        "--query", "-q", required=True, help="검색 쿼리 텍스트"
    )
    parser_search.add_argument(
        "--top-k", "-k", type=int, default=5, help="반환할 결과 수 (기본값: 5)"
    )
    parser_search.add_argument(
        "--file-filter", "-f", help="파일 경로 접두사로 결과 필터링"
    )
    parser_search.set_defaults(func=cmd_search)

    # stats 명령
    parser_stats = subparsers.add_parser("stats", help="인덱스 통계 표시")
    parser_stats.set_defaults(func=cmd_stats)

    # test 명령
    parser_test = subparsers.add_parser("test", help="테스트 실행")
    parser_test.add_argument(
        "-v", "--verbose", action="store_true", help="상세 출력"
    )
    parser_test.add_argument(
        "-k", "--pattern", help="특정 패턴의 테스트만 실행"
    )
    parser_test.add_argument(
        "--coverage", action="store_true", help="커버리지 리포트 생성"
    )
    parser_test.set_defaults(func=cmd_test)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
