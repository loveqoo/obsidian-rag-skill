"""obsidian_parser 모듈 테스트."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.obsidian_parser import (
    clean_content_for_embedding,
    extract_tags,
    extract_tags_from_frontmatter,
    extract_wikilinks,
    get_title_from_content,
    parse_frontmatter,
)


class TestParseFrontmatter:
    """parse_frontmatter 함수 테스트."""

    def test_정상적인_프론트매터_파싱(self):
        content = """---
title: 테스트
tags: [a, b]
---

본문 내용"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["title"] == "테스트"
        assert frontmatter["tags"] == ["a", "b"]
        assert body == "본문 내용"

    def test_프론트매터_없는_경우(self):
        content = "# 제목\n\n본문"
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def test_잘못된_프론트매터(self):
        content = """---
invalid: [unclosed
---

본문"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert "본문" in body


class TestExtractWikilinks:
    """extract_wikilinks 함수 테스트."""

    def test_기본_위키링크(self):
        content = "[[노트1]]과 [[노트2]] 링크"
        links = extract_wikilinks(content)

        assert "노트1" in links
        assert "노트2" in links

    def test_별칭_포함_위키링크(self):
        content = "[[노트|표시될 텍스트]] 링크"
        links = extract_wikilinks(content)

        assert "노트" in links

    def test_헤딩_포함_위키링크(self):
        content = "[[노트#섹션]] 링크"
        links = extract_wikilinks(content)

        assert "노트" in links

    def test_복합_위키링크(self):
        content = "[[노트#섹션|별칭]] 링크"
        links = extract_wikilinks(content)

        assert "노트" in links


class TestExtractTags:
    """extract_tags 함수 테스트."""

    def test_기본_태그(self):
        content = "#tag1 #tag2 본문"
        tags = extract_tags(content)

        assert "tag1" in tags
        assert "tag2" in tags

    def test_중첩_태그(self):
        content = "#parent/child/grandchild 태그"
        tags = extract_tags(content)

        assert "parent/child/grandchild" in tags

    def test_태그_중복_제거(self):
        content = "#tag1 #tag1 #tag1"
        tags = extract_tags(content)

        assert tags.count("tag1") == 1


class TestExtractTagsFromFrontmatter:
    """extract_tags_from_frontmatter 함수 테스트."""

    def test_리스트_형태_태그(self):
        frontmatter = {"tags": ["a", "b", "c"]}
        tags = extract_tags_from_frontmatter(frontmatter)

        assert tags == ["a", "b", "c"]

    def test_문자열_형태_태그(self):
        frontmatter = {"tags": "a, b, c"}
        tags = extract_tags_from_frontmatter(frontmatter)

        assert "a" in tags
        assert "b" in tags
        assert "c" in tags

    def test_태그_없는_경우(self):
        frontmatter = {}
        tags = extract_tags_from_frontmatter(frontmatter)

        assert tags == []


class TestGetTitleFromContent:
    """get_title_from_content 함수 테스트."""

    def test_프론트매터_타이틀_우선(self):
        content = "# 헤딩 제목"
        frontmatter = {"title": "프론트매터 제목"}

        title = get_title_from_content(content, frontmatter)
        assert title == "프론트매터 제목"

    def test_H1_헤딩에서_추출(self):
        content = "# 헤딩 제목\n\n본문"
        frontmatter = {}

        title = get_title_from_content(content, frontmatter)
        assert title == "헤딩 제목"

    def test_제목_없는_경우(self):
        content = "본문만 있음"
        frontmatter = {}

        title = get_title_from_content(content, frontmatter)
        assert title == ""


class TestCleanContentForEmbedding:
    """clean_content_for_embedding 함수 테스트."""

    def test_위키링크_텍스트_변환(self):
        content = "[[노트]]와 [[노트|별칭]] 링크"
        cleaned = clean_content_for_embedding(content)

        assert "[[" not in cleaned
        assert "노트" in cleaned
        assert "별칭" in cleaned

    def test_이미지_임베드_제거(self):
        content = "텍스트 ![[이미지.png]] 더 많은 텍스트"
        cleaned = clean_content_for_embedding(content)

        assert "![[" not in cleaned
        assert "이미지" not in cleaned

    def test_HTML_태그_제거(self):
        content = "<div>내용</div>"
        cleaned = clean_content_for_embedding(content)

        assert "<div>" not in cleaned
        assert "</div>" not in cleaned
        assert "내용" in cleaned

    def test_공백_정규화(self):
        content = "줄1\n\n\n\n줄2"
        cleaned = clean_content_for_embedding(content)

        assert "\n\n\n" not in cleaned
