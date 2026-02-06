# Obsidian RAG Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Git 기반 Obsidian Vault를 위한 시맨틱 검색 Claude Code 스킬입니다. ChromaDB와 임베딩을 활용하여 노트를 인덱싱하고 자연어로 검색할 수 있습니다.

## 주요 기능

- **시맨틱 검색**: 키워드 매칭이 아닌 의미 기반 검색
- **다국어 지원**: `paraphrase-multilingual-MiniLM-L12-v2` 임베딩 모델 사용 (한국어, 영어, 일본어, 중국어 등 50개 이상 언어 지원)
- **전체 인덱싱**: Vault의 모든 마크다운 파일을 한 번에 인덱싱
- **증분 업데이트**: 변경된 파일만 선택적으로 업데이트
- **Git 훅 지원**: push/pull 시 자동 인덱스 업데이트
- **Obsidian 메타데이터 파싱**: YAML frontmatter, 태그, 위키링크 추출

## 요구사항

- Python 3.9-3.12
- Git 저장소

## 빠른 시작

### 1. 설치

스킬을 처음 실행하면 자동으로 설치됩니다:
- Python 3.9-3.12 설치 (pyenv 사용, 필요 시)
- 가상 환경 생성 및 의존성 설치
- `.gitignore` 설정
- Git 훅 설치 (`pre-push`, `post-merge`)
- 프로젝트 루트에 `obsidian-rag` 간편 스크립트 생성

### 2. 사용법

모든 명령어는 **프로젝트 루트 디렉토리**에서 실행:

```bash
# 전체 인덱싱
./obsidian-rag full-index

# 검색
./obsidian-rag search --query "검색어" --top-k 5

# 증분 업데이트
./obsidian-rag incremental-update

# 통계
./obsidian-rag stats
```

## 명령어 목록

| 명령어 | 설명 |
|--------|------|
| `full-index` | 모든 마크다운 파일 인덱싱 |
| `incremental-update` | 변경된 파일만 업데이트 |
| `search --query "..." --top-k N` | 시맨틱 검색 (기본 top-k: 5) |
| `stats` | 인덱스 통계 확인 |
| `test` | 테스트 실행 |

## Git 훅 (자동 설치)

설치 시 자동으로 Git 훅이 설정됩니다:
- **pre-push**: 푸시 전 변경된 마크다운 파일 인덱싱
- **post-merge**: pull 후 새로 받은 마크다운 파일 인덱싱

## 디렉토리 구조

```
.claude/skills/obsidian-rag/
├── SKILL.md                 # 스킬 설명 파일
└── scripts/
    ├── setup.sh             # 설치 스크립트
    ├── install_hook.sh      # Git 훅 설치
    ├── uninstall.sh         # 제거 스크립트
    ├── obsidian_rag.py      # 메인 CLI
    ├── requirements.txt     # Python 의존성
    ├── lib/                 # 코어 라이브러리
    │   ├── chroma_manager.py
    │   ├── chunker.py
    │   ├── config.py
    │   ├── git_utils.py
    │   └── obsidian_parser.py
    └── tests/               # 테스트 파일
```

## 테스트 실행

```bash
# 기본 실행
./obsidian-rag test

# 상세 출력
./obsidian-rag test -v

# 특정 패턴 테스트만 실행
./obsidian-rag test -k "parser"
```

## 제거

```bash
.claude/skills/obsidian-rag/scripts/uninstall.sh
```

## 검색 결과 형식

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

## 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
