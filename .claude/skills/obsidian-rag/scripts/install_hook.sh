#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "=== Git 훅 설치 ==="

# Git 저장소인지 확인
if ! git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
    echo "오류: Git 저장소가 아닙니다."
    exit 1
fi

# hooks 디렉토리 생성
mkdir -p "$HOOKS_DIR"

# 훅 설치 함수
install_hook() {
    local HOOK_NAME=$1
    local HOOK_FILE="$HOOKS_DIR/$HOOK_NAME"
    local HOOK_CONTENT=$2

    # 기존 훅 백업
    if [[ -f "$HOOK_FILE" ]]; then
        if ! grep -q "# obsidian-rag-hook" "$HOOK_FILE"; then
            echo "기존 $HOOK_NAME 훅을 $HOOK_FILE.backup으로 백업 중"
            cp "$HOOK_FILE" "$HOOK_FILE.backup"
            CHAIN_EXISTING=true
        else
            echo "Obsidian RAG $HOOK_NAME 훅이 이미 설치됨. 업데이트 중..."
            CHAIN_EXISTING=false
        fi
    else
        CHAIN_EXISTING=false
    fi

    # 훅 스크립트 생성
    echo "$HOOK_CONTENT" > "$HOOK_FILE"

    # 기존 훅 체이닝
    if [[ "$CHAIN_EXISTING" == "true" ]]; then
        cat >> "$HOOK_FILE" << CHAINEOF

# 기존 $HOOK_NAME 훅 체이닝
if [[ -f "$HOOK_FILE.backup" ]]; then
    "$HOOK_FILE.backup" "\$@"
fi
CHAINEOF
    fi

    chmod +x "$HOOK_FILE"
    echo "설치됨: $HOOK_FILE"
}

# pre-push 훅 내용
PREPUSH_HOOK='#!/bin/bash
# obsidian-rag-hook

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SKILL_DIR="$PROJECT_ROOT/.claude/skills/obsidian-rag"
VENV_DIR="$SKILL_DIR/.venv"

# 푸시할 마크다운 파일 변경 확인
CHANGED_MD=$(git diff --cached --name-only --diff-filter=ACDMR | grep '\''\.md$'\'' || true)

if [[ -n "$CHANGED_MD" ]]; then
    echo "마크다운 파일 변경 감지. 증분 업데이트 실행 중..."

    if [[ -f "$VENV_DIR/bin/python" ]]; then
        "$VENV_DIR/bin/python" "$SKILL_DIR/scripts/obsidian_rag.py" incremental-update
    else
        echo "경고: Obsidian RAG 가상 환경을 찾을 수 없습니다. 증분 업데이트 건너뜀."
        echo "설치하려면 실행: $SKILL_DIR/scripts/setup.sh"
    fi
fi
'

# post-merge 훅 내용 (git pull 후 트리거)
POSTMERGE_HOOK='#!/bin/bash
# obsidian-rag-hook

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SKILL_DIR="$PROJECT_ROOT/.claude/skills/obsidian-rag"
VENV_DIR="$SKILL_DIR/.venv"

# 병합에서 변경된 마크다운 파일 확인
# ORIG_HEAD는 병합 전 커밋, HEAD는 병합 후 커밋
CHANGED_MD=$(git diff --name-only ORIG_HEAD HEAD | grep '\''\.md$'\'' || true)

if [[ -n "$CHANGED_MD" ]]; then
    echo "pull에서 마크다운 파일 변경 감지. 증분 업데이트 실행 중..."

    if [[ -f "$VENV_DIR/bin/python" ]]; then
        "$VENV_DIR/bin/python" "$SKILL_DIR/scripts/obsidian_rag.py" incremental-update
    else
        echo "경고: Obsidian RAG 가상 환경을 찾을 수 없습니다. 증분 업데이트 건너뜀."
        echo "설치하려면 실행: $SKILL_DIR/scripts/setup.sh"
    fi
fi
'

# 두 훅 모두 설치
install_hook "pre-push" "$PREPUSH_HOOK"
install_hook "post-merge" "$POSTMERGE_HOOK"

echo ""
echo "=== 훅 설치 완료 ==="
echo ""
echo "설치된 훅:"
echo "  - pre-push: 마크다운 변경 푸시 전 인덱스 업데이트"
echo "  - post-merge: 마크다운 변경 pull 후 인덱스 업데이트"
