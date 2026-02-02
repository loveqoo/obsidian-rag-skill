#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
HOOK_FILE="$HOOKS_DIR/pre-push"

echo "=== Installing Pre-push Hook ==="

# Check if we're in a git repository
if ! git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository."
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Backup existing hook if present
if [[ -f "$HOOK_FILE" ]]; then
    if ! grep -q "# obsidian-rag-hook" "$HOOK_FILE"; then
        echo "Backing up existing pre-push hook to $HOOK_FILE.backup"
        cp "$HOOK_FILE" "$HOOK_FILE.backup"
        CHAIN_EXISTING=true
    else
        echo "Obsidian RAG hook already installed. Updating..."
        CHAIN_EXISTING=false
    fi
else
    CHAIN_EXISTING=false
fi

# Create the hook script
cat > "$HOOK_FILE" << 'HOOKEOF'
#!/bin/bash
# obsidian-rag-hook

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SKILL_DIR="$PROJECT_ROOT/.claude/skills/obsidian-rag"
VENV_DIR="$SKILL_DIR/.venv"

# Check if there are any markdown file changes
CHANGED_MD=$(git diff --cached --name-only --diff-filter=ACDMR | grep '\.md$' || true)

if [[ -n "$CHANGED_MD" ]]; then
    echo "Detected markdown file changes. Running incremental update..."

    if [[ -f "$VENV_DIR/bin/python" ]]; then
        "$VENV_DIR/bin/python" "$SKILL_DIR/scripts/obsidian_rag.py" incremental-update
    else
        echo "Warning: Obsidian RAG virtual environment not found. Skipping incremental update."
        echo "Run setup.sh to install: $SKILL_DIR/scripts/setup.sh"
    fi
fi

HOOKEOF

# Chain existing hook if it was backed up
if [[ "$CHAIN_EXISTING" == "true" ]]; then
    cat >> "$HOOK_FILE" << CHAINEOF

# Chain to original pre-push hook
if [[ -f "$HOOK_FILE.backup" ]]; then
    "$HOOK_FILE.backup" "\$@"
fi
CHAINEOF
fi

chmod +x "$HOOK_FILE"

echo ""
echo "=== Hook Installation Complete ==="
echo "Pre-push hook installed at: $HOOK_FILE"
if [[ "$CHAIN_EXISTING" == "true" ]]; then
    echo "Original hook backed up to: $HOOK_FILE.backup"
fi
echo ""
echo "The hook will automatically run incremental-update when markdown files are pushed."
