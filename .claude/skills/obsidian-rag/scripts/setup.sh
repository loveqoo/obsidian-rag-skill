#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Get project root from current directory (supports running from any project)
PROJECT_ROOT="$(cd "$(pwd)" && git rev-parse --show-toplevel 2>/dev/null || echo ".")"
VENV_DIR="$SKILL_DIR/.venv"

echo "=== Obsidian RAG Setup ==="

# Check if Git repository
if ! git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a Git repository. Please run 'git init' first."
    exit 1
fi

# Check Python version (3.9-3.12 only, 3.13+ not supported by onnxruntime)
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

# Check pyenv requirement
if ! command -v pyenv > /dev/null 2>&1; then
    echo "Error: pyenv is not installed."
    echo ""
    echo "This skill requires pyenv for cross-platform compatibility."
    echo "Python 3.9-3.12 is required (3.13+ not supported by onnxruntime)."
    echo ""
    echo "Install pyenv:"
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
    echo "After installation: pyenv install 3.12"
    exit 1
fi

# Find suitable Python
PYTHON_CMD=""

echo "Checking for compatible Python versions in pyenv..."
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

# Auto-install if no compatible version found
if [[ -z "$PYTHON_CMD" ]]; then
    echo "No compatible Python version found in pyenv."
    echo "Auto-installing latest Python 3.12..."
    INSTALL_VERSION=$(pyenv install --list 2>/dev/null | grep -E "^\s*3\.12\." | tail -1 | tr -d ' ')
    if [[ -n "$INSTALL_VERSION" ]]; then
        echo "Installing Python $INSTALL_VERSION... (may take a few minutes)"
        pyenv install "$INSTALL_VERSION"
        PYENV_VERSION="$INSTALL_VERSION"
        export PYENV_VERSION
        PYTHON_CMD=$(pyenv which python 2>/dev/null || true)
        if [[ -n "$PYTHON_CMD" ]]; then
            echo "Python installation complete: $PYTHON_CMD (version $PYENV_VERSION)"
        fi
    else
        echo "Error: Could not find Python 3.12 in pyenv."
        exit 1
    fi
fi

if [[ -z "$PYTHON_CMD" ]]; then
    echo "Error: Python installation failed."
    echo "Please install manually: pyenv install 3.12"
    exit 1
fi

# Check and create virtual environment
if [[ -d "$VENV_DIR" ]]; then
    # Validate existing venv (both python and pip must be executable)
    if [[ -f "$VENV_DIR/bin/python" && -f "$VENV_DIR/bin/pip" ]] && \
       "$VENV_DIR/bin/python" --version > /dev/null 2>&1 && \
       "$VENV_DIR/bin/pip" --version > /dev/null 2>&1; then
        echo "Found existing virtual environment, skipping."
    else
        echo "Found corrupted virtual environment, recreating..."
        rm -rf "$VENV_DIR"
        "$PYTHON_CMD" -m venv "$VENV_DIR"
    fi
else
    echo "Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

# Install dependencies (direct execution without activation)
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip > /dev/null
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# Configure .gitignore
GITIGNORE="$PROJECT_ROOT/.gitignore"
GITIGNORE_BACKUP="$PROJECT_ROOT/.gitignore_backup"

if [[ -f "$GITIGNORE" && ! -f "$GITIGNORE_BACKUP" ]]; then
    echo "Backing up .gitignore to .gitignore_backup..."
    cp "$GITIGNORE" "$GITIGNORE_BACKUP"
fi

if [[ ! -f "$GITIGNORE" ]] || ! grep -q "^chroma_db/$" "$GITIGNORE"; then
    echo "Adding chroma_db/ to .gitignore..."
    echo "chroma_db/" >> "$GITIGNORE"
fi

if ! grep -q "^\.claude/skills/obsidian-rag/\.venv/$" "$GITIGNORE" 2>/dev/null; then
    echo "Adding .claude/skills/obsidian-rag/.venv/ to .gitignore..."
    echo ".claude/skills/obsidian-rag/.venv/" >> "$GITIGNORE"
fi

if ! grep -q "^\.obsidian_rag_config\.json$" "$GITIGNORE" 2>/dev/null; then
    echo "Adding .obsidian_rag_config.json to .gitignore..."
    echo ".obsidian_rag_config.json" >> "$GITIGNORE"
fi

if ! grep -q "^__pycache__/$" "$GITIGNORE" 2>/dev/null; then
    echo "Adding __pycache__/ to .gitignore..."
    echo "__pycache__/" >> "$GITIGNORE"
fi

# Auto-install Git hooks
echo ""
"$SCRIPT_DIR/install_hook.sh"

# Create convenience wrapper script (always create)
echo ""
echo "=== Creating Convenience Wrapper Script ==="
WRAPPER_SCRIPT="$PROJECT_ROOT/obsidian-rag"
cat > "$WRAPPER_SCRIPT" << 'WRAPPEREOF'
#!/bin/bash
# Obsidian RAG convenience wrapper script
# Auto-generated by setup.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/.claude/skills/obsidian-rag"
VENV_PYTHON="$SKILL_DIR/.venv/bin/python"
RAG_SCRIPT="$SKILL_DIR/scripts/obsidian_rag.py"

if [[ ! -f "$VENV_PYTHON" ]]; then
    echo "Error: Virtual environment not found."
    echo "Please run: $SKILL_DIR/scripts/setup.sh"
    exit 1
fi

exec "$VENV_PYTHON" "$RAG_SCRIPT" "$@"
WRAPPEREOF
chmod +x "$WRAPPER_SCRIPT"

# Add to .gitignore if not already there
GITIGNORE="$PROJECT_ROOT/.gitignore"
if ! grep -q "^obsidian-rag$" "$GITIGNORE" 2>/dev/null; then
    echo "obsidian-rag" >> "$GITIGNORE"
fi

echo "✓ Wrapper script created: $WRAPPER_SCRIPT"
echo ""
echo "Usage examples:"
echo "  ./obsidian-rag search --query \"search term\""
echo "  ./obsidian-rag full-index"
echo "  ./obsidian-rag incremental-update"
echo "  ./obsidian-rag stats"
echo ""
echo "💡 If you don't need this script, you can delete it: rm ./obsidian-rag"

echo ""
echo "=== Setup Complete ==="
echo "Virtual environment: $VENV_DIR"
