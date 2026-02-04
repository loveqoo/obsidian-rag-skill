"""chunker 모듈 테스트."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.chunker import Chunk, chunk_markdown_by_headers


class TestChunkMarkdownByHeaders:
    """chunk_markdown_by_headers 함수 테스트."""

    def test_기본_청킹(self):
        # 충분히 긴 콘텐츠로 여러 청크가 생성되도록 함
        long_content = "이것은 충분히 긴 내용입니다. " * 20
        content = f"""---
title: 테스트
tags: [test]
---

# 메인 제목

{long_content}

## 첫 번째 섹션

{long_content}

## 두 번째 섹션

{long_content}
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            f.flush()

            chunks = chunk_markdown_by_headers(Path(f.name))

            assert len(chunks) >= 2
            assert all(isinstance(c, Chunk) for c in chunks)

    def test_청크_메타데이터_포함(self):
        content = """---
title: 메타데이터 테스트
tags: [meta, test]
---

# 제목

내용 #inline-tag
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            f.flush()

            chunks = chunk_markdown_by_headers(Path(f.name))

            assert len(chunks) > 0
            chunk = chunks[0]
            assert chunk.metadata["title"] == "메타데이터 테스트"
            assert "meta" in chunk.metadata["tags"] or "test" in chunk.metadata["tags"]

    def test_큰_청크_분할(self):
        # 매우 긴 콘텐츠 생성
        long_paragraph = "이것은 테스트 문장입니다. " * 200
        content = f"""# 제목

{long_paragraph}

{long_paragraph}
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            f.flush()

            chunks = chunk_markdown_by_headers(
                Path(f.name), max_chunk_size=500
            )

            # 큰 콘텐츠가 여러 청크로 분할되어야 함
            assert len(chunks) > 1

    def test_작은_청크_병합(self):
        content = """# 제목

짧음

## 섹션1

짧음

## 섹션2

이것은 좀 더 긴 내용입니다. 충분히 길어야 합니다. 최소 청크 크기를 넘어야 합니다.
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            f.flush()

            chunks = chunk_markdown_by_headers(
                Path(f.name), min_chunk_size=50
            )

            # 작은 청크들이 병합되어야 함
            assert all(len(c.content) >= 10 for c in chunks)

    def test_청크_인덱스_연속성(self):
        content = """# 제목

내용1

## 섹션1

내용2

## 섹션2

내용3
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            f.flush()

            chunks = chunk_markdown_by_headers(Path(f.name))

            # 인덱스가 0부터 연속적이어야 함
            indices = [c.chunk_index for c in chunks]
            assert indices == list(range(len(chunks)))

    def test_위키링크_정제(self):
        content = """# 제목

[[노트링크]]와 [[다른노트|별칭]] 포함
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            f.flush()

            chunks = chunk_markdown_by_headers(Path(f.name))

            # 위키링크 문법이 제거되어야 함
            assert "[[" not in chunks[0].content
            assert "노트링크" in chunks[0].content or "별칭" in chunks[0].content
