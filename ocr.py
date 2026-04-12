"""
ocr.py — Image preprocessing and OCR text extraction using pytesseract.

Uses OpenCV for preprocessing and pytesseract (Tesseract wrapper) for OCR.
Tesseract is installed via build.sh. The binary path is set explicitly so
Render's runtime environment can find it regardless of PATH configuration.
"""

import os
import cv2
import numpy as np
import pytesseract
from PIL import Image

# Explicitly point pytesseract at the Tesseract binary.
# This is necessary on Render where the runtime PATH may differ from build PATH.
_TESSERACT_CANDIDATES = [
    "/usr/bin/tesseract",           # apt-get default on Debian/Ubuntu (Render)
    "/usr/local/bin/tesseract",     # alternate Linux location
    "/opt/homebrew/bin/tesseract",  # macOS Apple Silicon
    "/usr/local/Cellar/tesseract",  # macOS Intel Homebrew
]
for _candidate in _TESSERACT_CANDIDATES:
    if os.path.isfile(_candidate):
        pytesseract.pytesseract.tesseract_cmd = _candidate
        break


def preprocess_image(image_path: str):
    """
    Load and preprocess an image for better OCR accuracy.

    Steps:
        1. Load in grayscale.
        2. Upscale small images.
        3. Gaussian blur to reduce noise.
        4. Adaptive thresholding to binarize.
        5. Morphological cleanup.
    """
    pil_image = Image.open(image_path).convert("RGB")
    img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape
    if h < 300 or w < 300:
        scale = max(300 / h, 300 / w)
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)),
                          interpolation=cv2.INTER_CUBIC)

    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31, C=10,
    )
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    return cleaned


def extract_equation_from_image(image_path: str) -> str:
    """
    Run OCR on a preprocessed image and return the detected equation text.
    Tries PSM 6 and PSM 7 and picks the better result.
    """
    processed = preprocess_image(image_path)

    configs = [
        r"--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=+-*/^().²³ ",
        r"--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=+-*/^().²³ ",
    ]

    results = [_clean_raw_text(pytesseract.image_to_string(processed, config=c))
               for c in configs]
    return max(results, key=lambda t: len(t.strip())).strip()


def _clean_raw_text(text: str) -> str:
    """Remove noise characters from raw OCR output."""
    text = " ".join(text.replace("\n", " ").replace("\t", " ").split())
    allowed = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=+-*/^().²³ ")
    return "".join(ch for ch in text if ch in allowed).strip()
