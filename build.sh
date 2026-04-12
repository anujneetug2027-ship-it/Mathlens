#!/usr/bin/env bash
# build.sh — Render build script
set -e

echo "==> Installing Tesseract OCR..."
# Try sudo first (some Render environments need it, some don't)
if command -v sudo &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y tesseract-ocr
else
    apt-get update -y
    apt-get install -y tesseract-ocr
fi

echo "==> Tesseract installed at: $(which tesseract)"
echo "==> Tesseract version: $(tesseract --version 2>&1 | head -1)"

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Build complete."
