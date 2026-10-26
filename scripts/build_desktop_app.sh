#!/usr/bin/env bash
# Victory Crest ONE - Standalone Desktop App Builder (PyInstaller)
# Generates a standalone macOS .app bundle in dist/

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "📦 Checking PyInstaller..."
if ! .venv/bin/pip show pyinstaller &>/dev/null; then
    echo "Installing PyInstaller in virtual environment..."
    .venv/bin/pip install pyinstaller
fi

echo "🔨 Building standalone Victory Crest ONE application..."
.venv/bin/pyinstaller \
    --name="Victory Crest ONE" \
    --windowed \
    --noconfirm \
    --clean \
    --add-data="desktop:desktop" \
    --add-data="shared:shared" \
    --add-data="backend:backend" \
    --collect-all="PySide6" \
    desktop/main.py

echo "✅ Build Complete! You can find the application bundle in:"
echo "   $DIR/dist/Victory Crest ONE.app"
