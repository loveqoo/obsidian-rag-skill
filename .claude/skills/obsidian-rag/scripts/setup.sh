#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$SKILL_DIR/.venv"

echo "=== Obsidian RAG 설정 ==="

# Git 저장소인지 확인
if ! git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
    echo "오류: Git 저장소가 아닙니다. 먼저 git init을 실행하세요."
    exit 1
fi

# Python 버전 확인 함수
check_python_version() {
    local python_cmd=$1
    if command -v "$python_cmd" > /dev/null 2>&1; then
        local version=$("$python_cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        local major=$("$python_cmd" -c 'import sys; print(sys.version_info.major)')
        local minor=$("$python_cmd" -c 'import sys; print(sys.version_info.minor)')
        if [[ "$major" -eq 3 && "$minor" -ge 9 ]]; then
            echo "$python_cmd"
            return 0
        fi
    fi
    return 1
}

# 적합한 Python 찾기
PYTHON_CMD=""

# pyenv 먼저 시도
if command -v pyenv > /dev/null 2>&1; then
    echo "pyenv 발견, 호환 가능한 Python 버전 확인 중..."
    for version in 3.12 3.11 3.10 3.9; do
        if pyenv versions --bare | grep -q "^${version}"; then
            PYENV_VERSION=$(pyenv versions --bare | grep "^${version}" | tail -1)
            export PYENV_VERSION
            PYTHON_CMD=$(pyenv which python 2>/dev/null || true)
            if [[ -n "$PYTHON_CMD" ]]; then
                echo "pyenv Python 사용: $PYTHON_CMD (버전 $PYENV_VERSION)"
                break
            fi
        fi
    done
fi

# pyenv가 안 되면 시스템 Python 시도
if [[ -z "$PYTHON_CMD" ]]; then
    for cmd in python3.12 python3.11 python3.10 python3.9 python3 python; do
        if PYTHON_CMD=$(check_python_version "$cmd"); then
            echo "시스템 Python 사용: $PYTHON_CMD"
            break
        fi
    done
fi

if [[ -z "$PYTHON_CMD" ]]; then
    echo "오류: Python 3.9 이상이 필요하지만 찾을 수 없습니다."
    echo "pyenv 또는 시스템 패키지 관리자로 Python 3.9 이상을 설치하세요."
    exit 1
fi

# 가상 환경 생성
echo "가상 환경 생성 중..."
"$PYTHON_CMD" -m venv "$VENV_DIR"

# 활성화 및 의존성 설치
echo "의존성 설치 중..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip > /dev/null
pip install -r "$SCRIPT_DIR/requirements.txt"

# .gitignore 백업 및 수정
GITIGNORE="$PROJECT_ROOT/.gitignore"
GITIGNORE_BACKUP="$PROJECT_ROOT/.gitignore_backup"

# 기존 .gitignore가 있고 아직 백업이 없으면 백업 생성
if [[ -f "$GITIGNORE" && ! -f "$GITIGNORE_BACKUP" ]]; then
    echo ".gitignore를 .gitignore_backup으로 백업 중..."
    cp "$GITIGNORE" "$GITIGNORE_BACKUP"
fi

# .gitignore에 chroma_db 추가
if [[ ! -f "$GITIGNORE" ]] || ! grep -q "^chroma_db/$" "$GITIGNORE"; then
    echo ".gitignore에 chroma_db/ 추가 중..."
    echo "chroma_db/" >> "$GITIGNORE"
fi

# 스킬 내부 .venv도 무시
if ! grep -q "^\.claude/skills/obsidian-rag/\.venv/$" "$GITIGNORE"; then
    echo ".claude/skills/obsidian-rag/.venv/" >> "$GITIGNORE"
fi

echo ""
echo "=== 설정 완료 ==="
echo "가상 환경: $VENV_DIR"
echo ""
echo "스킬 사용법 - 환경 활성화:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "명령 실행:"
echo "  python $SCRIPT_DIR/obsidian_rag.py full-index"
echo "  python $SCRIPT_DIR/obsidian_rag.py search --query \"검색어\""
echo ""
echo "Git 훅 설치:"
echo "  $SCRIPT_DIR/install_hook.sh"
