"""Markdown chunking utilities for Obsidian RAG."""

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
    """A chunk of markdown content with metadata."""

    file_path: str
    chunk_index: int
    content: str
    heading: str
    heading_level: int
    metadata: dict


def chunk_markdown_by_headers(
    file_path: Path, min_chunk_size: int = 100, max_chunk_size: int = 2000
) -> list[Chunk]:
    """Split markdown file into chunks based on headers.

    Strategy:
    - Split on H1 and H2 headers
    - Keep content under headers together
    - Merge small chunks with previous chunk
    - Split overly large chunks by paragraphs
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter, body = parse_frontmatter(content)

    # Extract document-level metadata
    title = get_title_from_content(body, frontmatter)
    frontmatter_tags = extract_tags_from_frontmatter(frontmatter)
    all_wikilinks = extract_wikilinks(body)

    # Split by headers (H1 and H2)
    header_pattern = r"^(#{1,2})\s+(.+)$"
    lines = body.split("\n")

    sections: list[tuple[str, int, list[str]]] = []  # (heading, level, lines)
    current_heading = ""
    current_level = 0
    current_lines: list[str] = []

    for line in lines:
        match = re.match(header_pattern, line)
        if match:
            # Save previous section
            if current_lines or current_heading:
                sections.append((current_heading, current_level, current_lines))

            current_heading = match.group(2)
            current_level = len(match.group(1))
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    if current_lines or current_heading:
        sections.append((current_heading, current_level, current_lines))

    # Convert sections to chunks
    chunks: list[Chunk] = []
    file_path_str = str(file_path)

    for heading, level, section_lines in sections:
        section_content = "\n".join(section_lines).strip()

        if not section_content and not heading:
            continue

        # Clean content for embedding
        cleaned_content = clean_content_for_embedding(section_content)

        # Add heading to content for context
        if heading:
            full_content = f"{heading}\n\n{cleaned_content}" if cleaned_content else heading
        else:
            full_content = cleaned_content

        if not full_content:
            continue

        # Handle chunk size
        if len(full_content) > max_chunk_size:
            # Split large chunks by paragraphs
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
            # Merge small chunks with previous
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

    # Re-index chunks after merging
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
    """Create a chunk with metadata."""
    # Extract inline tags from this chunk
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
