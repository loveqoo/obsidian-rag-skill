"""Obsidian markdown parsing utilities."""

import re
from typing import Any

import yaml


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Returns:
        Tuple of (frontmatter dict, content without frontmatter)
    """
    if not content.startswith("---"):
        return {}, content

    lines = content.split("\n")
    end_index = -1

    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index == -1:
        return {}, content

    frontmatter_text = "\n".join(lines[1:end_index])
    remaining_content = "\n".join(lines[end_index + 1 :]).strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, remaining_content


def extract_wikilinks(content: str) -> list[str]:
    """Extract all wikilinks from content.

    Supported formats:
    - [[link]]
    - [[link|alias]]
    - [[link#heading]]
    - [[link#heading|alias]]
    """
    pattern = r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]"
    matches = re.findall(pattern, content)
    return list(set(matches))


def extract_tags(content: str) -> list[str]:
    """Extract all tags from content.

    Supported formats:
    - #tag
    - #tag/nested-tag
    - Frontmatter tags are handled separately
    """
    # Match #tag (excluding code blocks and URLs)
    pattern = r"(?<!\S)#([a-zA-Z][a-zA-Z0-9_/\-]*)"
    matches = re.findall(pattern, content)
    return list(set(matches))


def extract_tags_from_frontmatter(frontmatter: dict) -> list[str]:
    """Extract tags from frontmatter."""
    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        # Handle comma-separated tags
        tags = [t.strip() for t in tags.split(",")]
    elif not isinstance(tags, list):
        tags = []
    return [str(t) for t in tags if t]


def get_title_from_content(content: str, frontmatter: dict) -> str:
    """Extract title from frontmatter or first heading."""
    # Frontmatter title takes priority
    if frontmatter.get("title"):
        return str(frontmatter["title"])

    # Try first H1 heading
    lines = content.split("\n")
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()

    return ""


def clean_content_for_embedding(content: str) -> str:
    """Clean markdown content for embedding.

    Removes:
    - Wikilink syntax (keeps text)
    - Image embeds
    - Code blocks (optional)
    - Excessive whitespace
    """
    # Remove image embeds ![[...]]
    content = re.sub(r"!\[\[[^\]]+\]\]", "", content)

    # Convert wikilinks to plain text [[link|alias]] -> alias, [[link]] -> link
    content = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", content)
    content = re.sub(r"\[\[([^\]]+)\]\]", r"\1", content)

    # Remove markdown image syntax ![alt](url)
    content = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", content)

    # Convert markdown links to text [text](url) -> text
    content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)

    # Remove HTML tags
    content = re.sub(r"<[^>]+>", "", content)

    # Normalize whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = re.sub(r" {2,}", " ", content)

    return content.strip()
