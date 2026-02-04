#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "=== Obsidian RAG 제거 ==="

# 확인 메시지
read -p "정말로 Obsidian RAG 스킬을 제거하시겠습니까? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "제거가 취소되었습니다."
    exit 0
fi

# .gitignore 복원
GITIGNORE="$PROJECT_ROOT/.gitignore"
GITIGNORE_BACKUP="$PROJECT_ROOT/.gitignore_backup"

if [[ -f "$GITIGNORE_BACKUP" ]]; then
    echo ".gitignore_backup에서 .gitignore 복원 중..."
    mv "$GITIGNORE_BACKUP" "$GITIGNORE"
else
    echo "경고: .gitignore_backup 파일이 없습니다. .gitignore를 수동으로 확인하세요."
fi

# Git 훅 제거
echo "Git 훅 제거 중..."

for hook in pre-push post-merge; do
    HOOK_FILE="$HOOKS_DIR/$hook"
    HOOK_BACKUP="$HOOK_FILE.backup"

    if [[ -f "$HOOK_FILE" ]] && grep -q "# obsidian-rag-hook" "$HOOK_FILE"; then
        if [[ -f "$HOOK_BACKUP" ]]; then
            echo "  $hook 훅을 백업에서 복원 중..."
            mv "$HOOK_BACKUP" "$HOOK_FILE"
        else
            echo "  $hook 훅 제거 중..."
            rm "$HOOK_FILE"
        fi
    fi
done

# ChromaDB 삭제
CHROMA_DB="$PROJECT_ROOT/chroma_db"
if [[ -d "$CHROMA_DB" ]]; then
    echo "ChromaDB 데이터 삭제 중..."
    rm -rf "$CHROMA_DB"
fi

# 설정 파일 삭제
CONFIG_FILE="$PROJECT_ROOT/.obsidian_rag_config.json"
if [[ -f "$CONFIG_FILE" ]]; then
    echo "설정 파일 삭제 중..."
    rm "$CONFIG_FILE"
fi

# 스킬 폴더 삭제 여부 확인
read -p "스킬 폴더($SKILL_DIR)도 삭제하시겠습니까? (y/N): " delete_skill
if [[ "$delete_skill" == "y" || "$delete_skill" == "Y" ]]; then
    echo "스킬 폴더 삭제 중..."
    rm -rf "$SKILL_DIR"
    echo ""
    echo "=== 제거 완료 ==="
    echo "Obsidian RAG 스킬이 완전히 제거되었습니다."
else
    echo ""
    echo "=== 부분 제거 완료 ==="
    echo "스킬 폴더는 유지됩니다: $SKILL_DIR"
    echo "수동으로 삭제하려면: rm -rf $SKILL_DIR"
fi
