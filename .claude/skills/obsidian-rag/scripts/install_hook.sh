#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get project root from current directory (supports running from any project)
PROJECT_ROOT="$(cd "$(pwd)" && git rev-parse --show-toplevel 2>/dev/null || echo ".")"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "=== Installing Git Hooks ==="

# Check if Git repository
if ! git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a Git repository."
    exit 1
fi

# Create hooks directory
mkdir -p "$HOOKS_DIR"

# Hook installation function
install_hook() {
    local HOOK_NAME=$1
    local HOOK_FILE="$HOOKS_DIR/$HOOK_NAME"
    local HOOK_CONTENT=$2

    # Backup existing hook
    if [[ -f "$HOOK_FILE" ]]; then
        if ! grep -q "# obsidian-rag-hook" "$HOOK_FILE"; then
            echo "Backing up existing $HOOK_NAME hook to $HOOK_FILE.backup"
            cp "$HOOK_FILE" "$HOOK_FILE.backup"
            CHAIN_EXISTING=true
        else
            echo "Obsidian RAG $HOOK_NAME hook already installed. Updating..."
            CHAIN_EXISTING=false
        fi
    else
        CHAIN_EXISTING=false
    fi

    # Create hook script
    echo "$HOOK_CONTENT" > "$HOOK_FILE"

    # Chain existing hook
    if [[ "$CHAIN_EXISTING" == "true" ]]; then
        cat >> "$HOOK_FILE" << CHAINEOF

# Chain existing $HOOK_NAME hook
if [[ -f "$HOOK_FILE.backup" ]]; then
    "$HOOK_FILE.backup" "\$@"
fi
CHAINEOF
    fi

    chmod +x "$HOOK_FILE"
    echo "Installed: $HOOK_FILE"
}

# pre-push hook content
PREPUSH_HOOK='#!/bin/bash
# obsidian-rag-hook

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SKILL_DIR="$PROJECT_ROOT/.claude/skills/obsidian-rag"
VENV_DIR="$SKILL_DIR/.venv"

# Check for markdown file changes to push
CHANGED_MD=$(git diff --cached --name-only --diff-filter=ACDMR | grep '\''\.md$'\'' || true)

if [[ -n "$CHANGED_MD" ]]; then
    echo "Markdown file changes detected. Running incremental update..."

    if [[ -f "$VENV_DIR/bin/python" ]]; then
        "$VENV_DIR/bin/python" "$SKILL_DIR/scripts/obsidian_rag.py" incremental-update
    else
        echo "Warning: Obsidian RAG virtual environment not found. Skipping incremental update."
        echo "To install, run: $SKILL_DIR/scripts/setup.sh"
    fi
fi
'

# post-merge hook content (triggered after git pull)
POSTMERGE_HOOK='#!/bin/bash
# obsidian-rag-hook

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SKILL_DIR="$PROJECT_ROOT/.claude/skills/obsidian-rag"
VENV_DIR="$SKILL_DIR/.venv"

# Check for markdown file changes in merge
# ORIG_HEAD is pre-merge commit, HEAD is post-merge commit
CHANGED_MD=$(git diff --name-only ORIG_HEAD HEAD | grep '\''\.md$'\'' || true)

if [[ -n "$CHANGED_MD" ]]; then
    echo "Markdown file changes detected from pull. Running incremental update..."

    if [[ -f "$VENV_DIR/bin/python" ]]; then
        "$VENV_DIR/bin/python" "$SKILL_DIR/scripts/obsidian_rag.py" incremental-update
    else
        echo "Warning: Obsidian RAG virtual environment not found. Skipping incremental update."
        echo "To install, run: $SKILL_DIR/scripts/setup.sh"
    fi
fi
'

# Install both hooks
install_hook "pre-push" "$PREPUSH_HOOK"
install_hook "post-merge" "$POSTMERGE_HOOK"

echo ""
echo "=== Hook Installation Complete ==="
echo ""
echo "Installed hooks:"
echo "  - pre-push: Update index before pushing markdown changes"
echo "  - post-merge: Update index after pulling markdown changes"
