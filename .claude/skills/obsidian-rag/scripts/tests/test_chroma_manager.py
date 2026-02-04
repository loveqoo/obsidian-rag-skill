"""chroma_manager 모듈 테스트."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.chunker import Chunk
from lib.chroma_manager import ChromaManager


@pytest.fixture
def chroma_manager(temp_chroma_db):
    """테스트용 ChromaManager 인스턴스를 생성한다."""
    manager = ChromaManager(db_path=temp_chroma_db)
    yield manager
    manager.clear()


@pytest.fixture
def sample_chunks():
    """테스트용 샘플 청크를 생성한다."""
    return [
        Chunk(
            file_path="notes/test1.md",
            chunk_index=0,
            content="Python은 프로그래밍 언어입니다.",
            heading="Python 소개",
            heading_level=1,
            metadata={"title": "Python", "tags": ["python", "programming"]},
        ),
        Chunk(
            file_path="notes/test1.md",
            chunk_index=1,
            content="Python은 간단하고 읽기 쉽습니다.",
            heading="특징",
            heading_level=2,
            metadata={"title": "Python", "tags": ["python"]},
        ),
        Chunk(
            file_path="notes/test2.md",
            chunk_index=0,
            content="JavaScript는 웹 개발에 사용됩니다.",
            heading="JavaScript 소개",
            heading_level=1,
            metadata={"title": "JavaScript", "tags": ["javascript", "web"]},
        ),
    ]


class TestChromaManager:
    """ChromaManager 클래스 테스트."""

    def test_청크_추가(self, chroma_manager, sample_chunks):
        """청크 추가 테스트."""
        added = chroma_manager.add_chunks(sample_chunks)

        assert added == 3
        stats = chroma_manager.get_stats()
        assert stats["total_chunks"] == 3

    def test_빈_청크_추가(self, chroma_manager):
        """빈 청크 리스트 추가 테스트."""
        added = chroma_manager.add_chunks([])

        assert added == 0

    def test_검색(self, chroma_manager, sample_chunks):
        """검색 테스트."""
        chroma_manager.add_chunks(sample_chunks)

        results = chroma_manager.search("Python 프로그래밍", top_k=2)

        assert len(results) == 2
        # Python 관련 청크가 상위에 있어야 함
        assert any("Python" in r["content"] for r in results)

    def test_검색_결과_형식(self, chroma_manager, sample_chunks):
        """검색 결과 형식 테스트."""
        chroma_manager.add_chunks(sample_chunks)

        results = chroma_manager.search("test", top_k=1)

        assert len(results) > 0
        result = results[0]
        assert "file_path" in result
        assert "chunk_index" in result
        assert "content" in result
        assert "distance" in result
        assert "metadata" in result

    def test_파일_삭제(self, chroma_manager, sample_chunks):
        """파일 삭제 테스트."""
        chroma_manager.add_chunks(sample_chunks)

        deleted = chroma_manager.delete_file("notes/test1.md")

        assert deleted == 2  # test1.md에는 2개 청크
        stats = chroma_manager.get_stats()
        assert stats["total_chunks"] == 1  # test2.md의 1개만 남음

    def test_파일_업데이트(self, chroma_manager, sample_chunks):
        """파일 업데이트 테스트."""
        chroma_manager.add_chunks(sample_chunks)

        new_chunks = [
            Chunk(
                file_path="notes/test1.md",
                chunk_index=0,
                content="업데이트된 Python 내용",
                heading="새 제목",
                heading_level=1,
                metadata={"title": "Updated", "tags": []},
            )
        ]

        deleted, added = chroma_manager.update_file("notes/test1.md", new_chunks)

        assert deleted == 2  # 기존 2개 삭제
        assert added == 1  # 새로 1개 추가

        stats = chroma_manager.get_stats()
        assert stats["total_chunks"] == 2  # 1 (new) + 1 (test2.md)

    def test_전체_삭제(self, chroma_manager, sample_chunks):
        """전체 삭제 테스트."""
        chroma_manager.add_chunks(sample_chunks)

        cleared = chroma_manager.clear()

        assert cleared == 3
        stats = chroma_manager.get_stats()
        assert stats["total_chunks"] == 0

    def test_통계(self, chroma_manager, sample_chunks):
        """통계 테스트."""
        chroma_manager.add_chunks(sample_chunks)

        stats = chroma_manager.get_stats()

        assert stats["total_chunks"] == 3
        assert stats["collection_name"] == "obsidian_vault"
        assert "db_path" in stats

    def test_파일_필터_검색(self, chroma_manager, sample_chunks):
        """파일 필터 검색 테스트."""
        chroma_manager.add_chunks(sample_chunks)

        results = chroma_manager.search(
            "프로그래밍",
            top_k=5,
            file_filter="test1"
        )

        # test1.md 파일의 결과만 반환되어야 함
        for result in results:
            assert "test1" in result["file_path"]
