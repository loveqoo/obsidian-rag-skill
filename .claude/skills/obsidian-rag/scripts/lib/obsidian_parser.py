"""옵시디언 마크다운 파싱 유틸리티."""

import re
from typing import Any

import yaml


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """마크다운 콘텐츠에서 YAML 프론트매터를 파싱한다.

    Returns:
        (프론트매터 딕셔너리, 프론트매터 제외 콘텐츠) 튜플
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
    """콘텐츠에서 모든 위키링크를 추출한다.

    지원 형식:
    - [[링크]]
    - [[링크|별칭]]
    - [[링크#헤딩]]
    - [[링크#헤딩|별칭]]
    """
    pattern = r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]"
    matches = re.findall(pattern, content)
    return list(set(matches))


def extract_tags(content: str) -> list[str]:
    """콘텐츠에서 모든 태그를 추출한다.

    지원 형식:
    - #태그
    - #태그/중첩태그
    - 프론트매터의 태그는 별도 처리
    """
    # #태그 매칭 (코드 블록이나 URL 내부 제외)
    pattern = r"(?<!\S)#([a-zA-Z][a-zA-Z0-9_/\-]*)"
    matches = re.findall(pattern, content)
    return list(set(matches))


def extract_tags_from_frontmatter(frontmatter: dict) -> list[str]:
    """프론트매터에서 태그를 추출한다."""
    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        # 쉼표로 구분된 태그 처리
        tags = [t.strip() for t in tags.split(",")]
    elif not isinstance(tags, list):
        tags = []
    return [str(t) for t in tags if t]


def get_title_from_content(content: str, frontmatter: dict) -> str:
    """프론트매터 또는 첫 번째 헤딩에서 제목을 추출한다."""
    # 프론트매터 title 우선
    if frontmatter.get("title"):
        return str(frontmatter["title"])

    # 첫 번째 H1 헤딩 시도
    lines = content.split("\n")
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()

    return ""


def clean_content_for_embedding(content: str) -> str:
    """임베딩을 위해 마크다운 콘텐츠를 정제한다.

    제거 항목:
    - 위키링크 문법 (텍스트는 유지)
    - 이미지 임베드
    - 코드 블록 (선택적)
    - 과도한 공백
    """
    # 이미지 임베드 제거 ![[...]]
    content = re.sub(r"!\[\[[^\]]+\]\]", "", content)

    # 위키링크를 일반 텍스트로 변환 [[링크|별칭]] -> 별칭, [[링크]] -> 링크
    content = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", content)
    content = re.sub(r"\[\[([^\]]+)\]\]", r"\1", content)

    # 마크다운 이미지 문법 제거 ![alt](url)
    content = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", content)

    # 마크다운 링크를 텍스트로 변환 [텍스트](url) -> 텍스트
    content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)

    # HTML 태그 제거
    content = re.sub(r"<[^>]+>", "", content)

    # 공백 정규화
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = re.sub(r" {2,}", " ", content)

    return content.strip()
