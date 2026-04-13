"""
ocr.py — OCR via Google Gemini Vision API (free tier available).

Sends the image to Gemini 2.5 Flash and extracts the math equation.
No system dependencies required — works on any cloud platform.
"""

import os
import base64
import google.generativeai as genai
from PIL import Image


def extract_equation_from_image(image_path: str) -> str:
    """
    Extract a math equation from an image using Gemini Vision.

    Args:
        image_path: Path to the uploaded image file.

    Returns:
        The detected equation as a plain text string.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

    image = Image.open(image_path)

    response = model.generate_content([
        image,
        (
            "Extract the mathematical equation from this image. "
            "Return ONLY the equation as plain text, nothing else. "
            "Use standard ASCII characters: "
            "^ for exponents (e.g. x^2), * for multiplication. "
            "Do not include any explanation or extra words. "
            "Example output: x^2 - 13x + 42 = 0"
        ),
    ])

    return response.text.strip()
