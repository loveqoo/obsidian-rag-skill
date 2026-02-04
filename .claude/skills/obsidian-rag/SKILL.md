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

### 통계
인덱스 통계를 확인합니다.
```bash
python scripts/obsidian_rag.py stats
```

### 테스트
테스트를 실행하여 기능을 검증합니다.
```bash
python scripts/obsidian_rag.py test           # 기본 실행
python scripts/obsidian_rag.py test -v        # 상세 출력
python scripts/obsidian_rag.py test -k "파서"  # 특정 패턴 테스트만 실행
```

## Git 훅 설치
Git 훅을 설치하여 push/pull 시 자동으로 인덱스를 업데이트합니다.
```bash
./scripts/install_hook.sh
```

설치되는 훅:
- **pre-push**: 푸시 전 변경된 마크다운 파일 인덱싱
- **post-merge**: pull 후 새로 받은 마크다운 파일 인덱싱

## 제거
스킬을 완전히 제거하고 원래 상태로 복원합니다.
```bash
./scripts/uninstall.sh
```

제거 시 처리되는 항목:
- `.gitignore` → `.gitignore_backup`에서 복원
- Git 훅 (pre-push, post-merge) 제거 또는 복원
- ChromaDB 데이터 삭제
- 설정 파일 삭제
- 스킬 폴더 삭제 (선택)

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
