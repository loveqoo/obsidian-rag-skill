---
name: obsidian-rag
description: Git 기반 옵시디언 Vault의 시맨틱 검색. 전체 인덱싱, 증분 업데이트, 검색 기능 제공.
---

# Obsidian RAG Skill

Git 저장소 기반 옵시디언 Vault에서 동작하는 RAG(Retrieval-Augmented Generation) 스킬입니다.

## 요구사항
- Python 3.9-3.12
- Git 저장소

## 설치
```bash
cd .claude/skills/obsidian-rag/scripts
./setup.sh
```

## 사용법

### 전체 인덱싱
Vault의 모든 마크다운 파일을 인덱싱합니다.
```bash
python scripts/obsidian_rag.py full-index
```

### 증분 업데이트
마지막 인덱싱 이후 변경된 파일만 업데이트합니다.
```bash
python scripts/obsidian_rag.py incremental-update
```

### 검색
시맨틱 검색을 수행하고 JSON 형식으로 결과를 반환합니다.
```bash
python scripts/obsidian_rag.py search --query "검색어" --top-k 5
```

## Git 훅 설치
pre-push 훅을 설치하여 푸시 전 자동으로 증분 업데이트를 실행합니다.
```bash
./scripts/install_hook.sh
```

## 출력 형식
검색 결과는 JSON 형식으로 출력됩니다:
```json
{
  "query": "검색어",
  "results": [
    {
      "file_path": "notes/example.md",
      "chunk_index": 0,
      "content": "관련 내용...",
      "distance": 0.234,
      "metadata": {
        "title": "Example Note",
        "tags": ["tag1", "tag2"]
      }
    }
  ],
  "total": 5
}
```
