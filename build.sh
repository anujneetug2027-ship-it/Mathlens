#!/usr/bin/env bash
# build.sh — Render build script
# Installs the Tesseract OCR system binary (requires root via sudo),
# then installs Python dependencies.
set -e  # exit immediately on any error

echo "==> Installing Tesseract OCR system package..."
sudo apt-get update -qq
sudo apt-get install -y tesseract-ocr

echo "==> Tesseract version:"
tesseract --version

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Build complete."
