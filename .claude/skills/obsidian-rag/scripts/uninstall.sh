#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "=== Obsidian RAG Uninstallation ==="

# Confirmation prompt
read -p "Are you sure you want to uninstall Obsidian RAG skill? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Restore .gitignore
GITIGNORE="$PROJECT_ROOT/.gitignore"
GITIGNORE_BACKUP="$PROJECT_ROOT/.gitignore_backup"

if [[ -f "$GITIGNORE_BACKUP" ]]; then
    echo "Restoring .gitignore from .gitignore_backup..."
    mv "$GITIGNORE_BACKUP" "$GITIGNORE"
else
    echo "Warning: .gitignore_backup not found. Please check .gitignore manually."
fi

# Remove Git hooks
echo "Removing Git hooks..."

for hook in pre-push post-merge; do
    HOOK_FILE="$HOOKS_DIR/$hook"
    HOOK_BACKUP="$HOOK_FILE.backup"

    if [[ -f "$HOOK_FILE" ]] && grep -q "# obsidian-rag-hook" "$HOOK_FILE"; then
        if [[ -f "$HOOK_BACKUP" ]]; then
            echo "  Restoring $hook hook from backup..."
            mv "$HOOK_BACKUP" "$HOOK_FILE"
        else
            echo "  Removing $hook hook..."
            rm "$HOOK_FILE"
        fi
    fi
done

# Delete ChromaDB
CHROMA_DB="$PROJECT_ROOT/chroma_db"
if [[ -d "$CHROMA_DB" ]]; then
    echo "Deleting ChromaDB data..."
    rm -rf "$CHROMA_DB"
fi

# Delete config file
CONFIG_FILE="$PROJECT_ROOT/.obsidian_rag_config.json"
if [[ -f "$CONFIG_FILE" ]]; then
    echo "Deleting config file..."
    rm "$CONFIG_FILE"
fi

# Confirm skill folder deletion
read -p "Delete skill folder ($SKILL_DIR) as well? (y/N): " delete_skill
if [[ "$delete_skill" == "y" || "$delete_skill" == "Y" ]]; then
    echo "Deleting skill folder..."
    rm -rf "$SKILL_DIR"
    echo ""
    echo "=== Uninstallation Complete ==="
    echo "Obsidian RAG skill has been completely removed."
else
    echo ""
    echo "=== Partial Uninstallation Complete ==="
    echo "Skill folder retained: $SKILL_DIR"
    echo "To delete manually: rm -rf $SKILL_DIR"
fi
