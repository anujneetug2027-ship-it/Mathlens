"""
ocr.py — Image preprocessing and OCR text extraction.

Uses OpenCV for preprocessing (grayscale, thresholding, denoising)
and pytesseract for Optical Character Recognition.
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Load and preprocess an image for better OCR accuracy.

    Steps:
        1. Load the image in grayscale.
        2. Upscale small images so Tesseract works better.
        3. Apply Gaussian blur to reduce noise.
        4. Apply adaptive thresholding to binarize the image.
        5. Apply morphological operations to clean up artifacts.

    Args:
        image_path: Path to the uploaded image file.

    Returns:
        A preprocessed NumPy array (grayscale, binarized image).
    """
    # Load image using PIL first (handles more formats), then convert to NumPy
    pil_image = Image.open(image_path).convert("RGB")
    img = np.array(pil_image)

    # Convert RGB to BGR for OpenCV compatibility
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Upscale if the image is too small (Tesseract struggles below ~300px height)
    h, w = gray.shape
    if h < 300 or w < 300:
        scale = max(300 / h, 300 / w)
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    # Slight Gaussian blur to reduce noise before thresholding
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Adaptive thresholding — handles uneven lighting better than global threshold
    thresh = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=10,
    )

    # Morphological opening to remove small noise speckles
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

    return cleaned


def extract_equation_from_image(image_path: str) -> str:
    """
    Run OCR on a preprocessed image and return the detected equation text.

    Tries two Tesseract configurations and picks the more informative result:
      - PSM 6: Assumes a uniform block of text (good for single-line equations).
      - PSM 7: Treats the image as a single text line.

    Args:
        image_path: Path to the uploaded image file.

    Returns:
        Cleaned equation string extracted from the image.
    """
    processed = preprocess_image(image_path)

    # Tesseract config: allow digits, letters, and common math characters
    # PSM 6 = single block of text; PSM 7 = single line
    custom_configs = [
        r"--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=+-*/^().² ³",
        r"--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=+-*/^().² ³",
    ]

    results = []
    for config in custom_configs:
        text = pytesseract.image_to_string(processed, config=config)
        cleaned = _clean_raw_text(text)
        results.append(cleaned)

    # Pick the result that contains more meaningful characters
    best = max(results, key=lambda t: len(t.strip()))
    return best.strip()


def _clean_raw_text(text: str) -> str:
    """
    Remove noise characters from raw OCR output.

    Args:
        text: Raw string from pytesseract.

    Returns:
        Lightly cleaned string ready for the parser.
    """
    # Remove newlines and tabs, collapse multiple spaces
    text = text.replace("\n", " ").replace("\t", " ")
    text = " ".join(text.split())

    # Remove stray characters that are clearly OCR artifacts
    allowed = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=+-*/^().²³ ")
    text = "".join(ch for ch in text if ch in allowed)

    return text.strip()
