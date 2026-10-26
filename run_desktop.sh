#!/usr/bin/env bash
# Victory Crest ONE - Desktop Application Quick Launcher
# Usage: ./run_desktop.sh [optional arguments]

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Check virtual environment
if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
else
    echo "❌ Error: Python 3 not found. Please activate your virtual environment."
    exit 1
fi

echo "🚀 Launching Victory Crest ONE Desktop Application..."
"$PYTHON_BIN" desktop/main.py "$@"
