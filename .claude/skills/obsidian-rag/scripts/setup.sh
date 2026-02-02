#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$SKILL_DIR/.venv"

echo "=== Obsidian RAG Setup ==="

# Check if we're in a git repository
if ! git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository. Please initialize git first."
    exit 1
fi

# Check Python version
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

# Find suitable Python
PYTHON_CMD=""

# Try pyenv first
if command -v pyenv > /dev/null 2>&1; then
    echo "Found pyenv, checking for compatible Python version..."
    for version in 3.12 3.11 3.10 3.9; do
        if pyenv versions --bare | grep -q "^${version}"; then
            PYENV_VERSION=$(pyenv versions --bare | grep "^${version}" | tail -1)
            export PYENV_VERSION
            PYTHON_CMD=$(pyenv which python 2>/dev/null || true)
            if [[ -n "$PYTHON_CMD" ]]; then
                echo "Using pyenv Python: $PYTHON_CMD (version $PYENV_VERSION)"
                break
            fi
        fi
    done
fi

# Try system Python if pyenv didn't work
if [[ -z "$PYTHON_CMD" ]]; then
    for cmd in python3.12 python3.11 python3.10 python3.9 python3 python; do
        if PYTHON_CMD=$(check_python_version "$cmd"); then
            echo "Using system Python: $PYTHON_CMD"
            break
        fi
    done
fi

if [[ -z "$PYTHON_CMD" ]]; then
    echo "Error: Python 3.9+ is required but not found."
    echo "Please install Python 3.9 or newer using pyenv or your system package manager."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
"$PYTHON_CMD" -m venv "$VENV_DIR"

# Activate and install dependencies
echo "Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip > /dev/null
pip install -r "$SCRIPT_DIR/requirements.txt"

# Add chroma_db to .gitignore if not already present
GITIGNORE="$PROJECT_ROOT/.gitignore"
if [[ ! -f "$GITIGNORE" ]] || ! grep -q "^chroma_db/$" "$GITIGNORE"; then
    echo "Adding chroma_db/ to .gitignore..."
    echo "chroma_db/" >> "$GITIGNORE"
fi

# Also ignore the .venv inside the skill
if ! grep -q "^\.claude/skills/obsidian-rag/\.venv/$" "$GITIGNORE"; then
    echo ".claude/skills/obsidian-rag/.venv/" >> "$GITIGNORE"
fi

echo ""
echo "=== Setup Complete ==="
echo "Virtual environment: $VENV_DIR"
echo ""
echo "To use the skill, activate the environment:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "Then run commands:"
echo "  python $SCRIPT_DIR/obsidian_rag.py full-index"
echo "  python $SCRIPT_DIR/obsidian_rag.py search --query \"your query\""
echo ""
echo "To install the pre-push hook:"
echo "  $SCRIPT_DIR/install_hook.sh"
