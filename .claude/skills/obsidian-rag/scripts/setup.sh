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

# Python 버전 확인 함수 (3.9~3.12만 허용, 3.13+는 onnxruntime 미지원)
check_python_version() {
    local python_cmd=$1
    if command -v "$python_cmd" > /dev/null 2>&1; then
        local major=$("$python_cmd" -c 'import sys; print(sys.version_info.major)')
        local minor=$("$python_cmd" -c 'import sys; print(sys.version_info.minor)')
        if [[ "$major" -eq 3 && "$minor" -ge 9 && "$minor" -le 12 ]]; then
            echo "$python_cmd"
            return 0
        fi
    fi
    return 1
}

# pyenv 필수 확인
if ! command -v pyenv > /dev/null 2>&1; then
    echo "오류: pyenv가 설치되어 있지 않습니다."
    echo ""
    echo "이 스킬은 크로스 플랫폼 호환성을 위해 pyenv를 사용합니다."
    echo "Python 3.9~3.12가 필요합니다 (3.13+ onnxruntime 미지원)."
    echo ""
    echo "pyenv 설치 방법:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install pyenv"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  curl https://pyenv.run | bash"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "  https://github.com/pyenv-win/pyenv-win#installation"
    else
        echo "  https://github.com/pyenv/pyenv#installation"
    fi
    echo ""
    echo "설치 후: pyenv install 3.12"
    exit 1
fi

# 적합한 Python 찾기
PYTHON_CMD=""

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

# pyenv에 적합한 버전이 없으면 자동 설치
if [[ -z "$PYTHON_CMD" ]]; then
    echo "pyenv에 호환 가능한 Python 버전이 없습니다."
    echo "Python 3.12 최신 버전을 자동 설치합니다..."
    INSTALL_VERSION=$(pyenv install --list 2>/dev/null | grep -E "^\s*3\.12\." | tail -1 | tr -d ' ')
    if [[ -n "$INSTALL_VERSION" ]]; then
        echo "Python $INSTALL_VERSION 설치 중... (몇 분 소요될 수 있습니다)"
        pyenv install "$INSTALL_VERSION"
        PYENV_VERSION="$INSTALL_VERSION"
        export PYENV_VERSION
        PYTHON_CMD=$(pyenv which python 2>/dev/null || true)
        if [[ -n "$PYTHON_CMD" ]]; then
            echo "pyenv Python 설치 완료: $PYTHON_CMD (버전 $PYENV_VERSION)"
        fi
    else
        echo "오류: pyenv에서 Python 3.12 버전을 찾을 수 없습니다."
        exit 1
    fi
fi

if [[ -z "$PYTHON_CMD" ]]; then
    echo "오류: Python 설치에 실패했습니다."
    echo "수동으로 설치하세요: pyenv install 3.12"
    exit 1
fi

# 가상 환경 확인 및 생성
if [[ -d "$VENV_DIR" ]]; then
    # 기존 venv가 있으면 유효성 검사 (python과 pip 모두 실행 가능해야 함)
    if [[ -f "$VENV_DIR/bin/python" && -f "$VENV_DIR/bin/pip" ]] && \
       "$VENV_DIR/bin/python" --version > /dev/null 2>&1 && \
       "$VENV_DIR/bin/pip" --version > /dev/null 2>&1; then
        echo "기존 가상 환경 발견, 건너뜀."
    else
        echo "손상된 가상 환경 발견, 재생성 중..."
        rm -rf "$VENV_DIR"
        "$PYTHON_CMD" -m venv "$VENV_DIR"
    fi
else
    echo "가상 환경 생성 중..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

# 의존성 설치 (activate 없이 직접 실행)
echo "의존성 설치 중..."
"$VENV_DIR/bin/pip" install --upgrade pip > /dev/null
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# .gitignore 설정
GITIGNORE="$PROJECT_ROOT/.gitignore"
GITIGNORE_BACKUP="$PROJECT_ROOT/.gitignore_backup"

if [[ -f "$GITIGNORE" && ! -f "$GITIGNORE_BACKUP" ]]; then
    echo ".gitignore를 .gitignore_backup으로 백업 중..."
    cp "$GITIGNORE" "$GITIGNORE_BACKUP"
fi

if [[ ! -f "$GITIGNORE" ]] || ! grep -q "^chroma_db/$" "$GITIGNORE"; then
    echo ".gitignore에 chroma_db/ 추가 중..."
    echo "chroma_db/" >> "$GITIGNORE"
fi

if ! grep -q "^\.claude/skills/obsidian-rag/\.venv/$" "$GITIGNORE" 2>/dev/null; then
    echo ".gitignore에 .claude/skills/obsidian-rag/.venv/ 추가 중..."
    echo ".claude/skills/obsidian-rag/.venv/" >> "$GITIGNORE"
fi

if ! grep -q "^\.obsidian_rag_config\.json$" "$GITIGNORE" 2>/dev/null; then
    echo ".gitignore에 .obsidian_rag_config.json 추가 중..."
    echo ".obsidian_rag_config.json" >> "$GITIGNORE"
fi

if ! grep -q "^__pycache__/$" "$GITIGNORE" 2>/dev/null; then
    echo ".gitignore에 __pycache__/ 추가 중..."
    echo "__pycache__/" >> "$GITIGNORE"
fi

# Git 훅 자동 설치
echo ""
"$SCRIPT_DIR/install_hook.sh"

echo ""
echo "=== 설정 완료 ==="
echo "가상 환경: $VENV_DIR"
