#!/usr/bin/env bash
# Double-clickable macOS launcher for Victory Crest ONE Desktop
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -f ".venv/bin/python" ]; then
    .venv/bin/python desktop/main.py
else
    python3 desktop/main.py
fi
