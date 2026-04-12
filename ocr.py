"""
ocr.py — Image preprocessing and OCR extraction using EasyOCR.

EasyOCR is a pure-Python OCR library — no system binary (like Tesseract) is
required. This makes it ideal for cloud deployments like Render where
apt-get access is restricted.
"""

import cv2
import numpy as np
import easyocr
from PIL import Image

# Initialise the EasyOCR reader once (downloads model on first run, ~100 MB).
# english only; gpu=False ensures CPU-only mode (Render free tier has no GPU).
_reader = None


def _get_reader() -> easyocr.Reader:
    """Lazy-load the EasyOCR reader so startup is fast."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Load and preprocess an image for better OCR accuracy.

    Steps:
        1. Load the image in grayscale.
        2. Upscale small images.
        3. Apply Gaussian blur to reduce noise.
        4. Apply adaptive thresholding to binarize.
        5. Morphological cleanup.

    Args:
        image_path: Path to the uploaded image file.

    Returns:
        A preprocessed NumPy array (grayscale, binarized).
    """
    pil_image = Image.open(image_path).convert("RGB")
    img = np.array(pil_image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Upscale tiny images
    h, w = gray.shape
    if h < 300 or w < 300:
        scale = max(300 / h, 300 / w)
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

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
    Run OCR on the image and return the detected equation text.

    Uses EasyOCR — no Tesseract binary required.

    Args:
        image_path: Path to the uploaded image file.

    Returns:
        Cleaned equation string.
    """
    processed = preprocess_image(image_path)

    reader = _get_reader()

    # EasyOCR accepts a NumPy array directly
    results = reader.readtext(processed, detail=0, paragraph=True)

    raw_text = " ".join(results)
    return _clean_raw_text(raw_text).strip()


def _clean_raw_text(text: str) -> str:
    """Remove noise characters from raw OCR output."""
    text = text.replace("\n", " ").replace("\t", " ")
    text = " ".join(text.split())

    allowed = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=+-*/^().²³ ")
    text = "".join(ch for ch in text if ch in allowed)

    return text.strip()
