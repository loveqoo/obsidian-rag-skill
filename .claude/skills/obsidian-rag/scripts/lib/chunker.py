"""Obsidian RAG용 마크다운 청킹 유틸리티."""

import re
from dataclasses import dataclass
from pathlib import Path

from .obsidian_parser import (
    clean_content_for_embedding,
    extract_tags,
    extract_tags_from_frontmatter,
    extract_wikilinks,
    get_title_from_content,
    parse_frontmatter,
)


@dataclass
class Chunk:
    """메타데이터를 포함한 마크다운 콘텐츠 청크."""

    file_path: str
    chunk_index: int
    content: str
    heading: str
    heading_level: int
    metadata: dict


def chunk_markdown_by_headers(
    file_path: Path, min_chunk_size: int = 100, max_chunk_size: int = 2000
) -> list[Chunk]:
    """마크다운 파일을 헤더 기준으로 청크로 분할한다.

    전략:
    - H1, H2 헤더 기준으로 분할
    - 헤더 아래 콘텐츠는 함께 유지
    - 작은 청크는 이전 청크와 병합
    - 큰 청크는 문단 단위로 분할
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter, body = parse_frontmatter(content)

    # 문서 레벨 메타데이터 추출
    title = get_title_from_content(body, frontmatter)
    frontmatter_tags = extract_tags_from_frontmatter(frontmatter)
    all_wikilinks = extract_wikilinks(body)

    # 헤더 기준 분할 (H1, H2)
    header_pattern = r"^(#{1,2})\s+(.+)$"
    lines = body.split("\n")

    sections: list[tuple[str, int, list[str]]] = []  # (헤딩, 레벨, 라인들)
    current_heading = ""
    current_level = 0
    current_lines: list[str] = []

    for line in lines:
        match = re.match(header_pattern, line)
        if match:
            # 이전 섹션 저장
            if current_lines or current_heading:
                sections.append((current_heading, current_level, current_lines))

            current_heading = match.group(2)
            current_level = len(match.group(1))
            current_lines = []
        else:
            current_lines.append(line)

    # 마지막 섹션 저장
    if current_lines or current_heading:
        sections.append((current_heading, current_level, current_lines))

    # 섹션을 청크로 변환
    chunks: list[Chunk] = []
    file_path_str = str(file_path)

    for heading, level, section_lines in sections:
        section_content = "\n".join(section_lines).strip()

        if not section_content and not heading:
            continue

        # 임베딩용 콘텐츠 정제
        cleaned_content = clean_content_for_embedding(section_content)

        # 컨텍스트를 위해 헤딩을 콘텐츠에 추가
        if heading:
            full_content = f"{heading}\n\n{cleaned_content}" if cleaned_content else heading
        else:
            full_content = cleaned_content

        if not full_content:
            continue

        # 청크 크기 처리
        if len(full_content) > max_chunk_size:
            # 큰 청크는 문단 단위로 분할
            paragraphs = full_content.split("\n\n")
            current_chunk_content = ""

            for para in paragraphs:
                if len(current_chunk_content) + len(para) + 2 > max_chunk_size:
                    if current_chunk_content:
                        chunks.append(
                            _create_chunk(
                                file_path_str,
                                len(chunks),
                                current_chunk_content,
                                heading,
                                level,
                                title,
                                frontmatter_tags,
                                frontmatter,
                            )
                        )
                    current_chunk_content = para
                else:
                    if current_chunk_content:
                        current_chunk_content += "\n\n" + para
                    else:
                        current_chunk_content = para

            if current_chunk_content:
                chunks.append(
                    _create_chunk(
                        file_path_str,
                        len(chunks),
                        current_chunk_content,
                        heading,
                        level,
                        title,
                        frontmatter_tags,
                        frontmatter,
                    )
                )
        elif len(full_content) < min_chunk_size and chunks:
            # 작은 청크는 이전 청크와 병합
            prev_chunk = chunks[-1]
            merged_content = prev_chunk.content + "\n\n" + full_content
            chunks[-1] = Chunk(
                file_path=prev_chunk.file_path,
                chunk_index=prev_chunk.chunk_index,
                content=merged_content,
                heading=prev_chunk.heading,
                heading_level=prev_chunk.heading_level,
                metadata=prev_chunk.metadata,
            )
        else:
            chunks.append(
                _create_chunk(
                    file_path_str,
                    len(chunks),
                    full_content,
                    heading,
                    level,
                    title,
                    frontmatter_tags,
                    frontmatter,
                )
            )

    # 병합 후 청크 인덱스 재정렬
    for i, chunk in enumerate(chunks):
        chunk.chunk_index = i

    return chunks


def _create_chunk(
    file_path: str,
    chunk_index: int,
    content: str,
    heading: str,
    level: int,
    title: str,
    frontmatter_tags: list[str],
    frontmatter: dict,
) -> Chunk:
    """메타데이터를 포함한 청크를 생성한다."""
    # 이 청크에서 인라인 태그 추출
    inline_tags = extract_tags(content)
    all_tags = list(set(frontmatter_tags + inline_tags))

    metadata = {
        "title": title,
        "tags": all_tags,
        "frontmatter": {k: v for k, v in frontmatter.items() if k not in ("tags", "title")},
    }

    return Chunk(
        file_path=file_path,
        chunk_index=chunk_index,
        content=content,
        heading=heading,
        heading_level=level,
        metadata=metadata,
    )
