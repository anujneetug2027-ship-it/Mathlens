"""
ocr.py — OCR via Google Gemini Vision API.
Uses the new google-genai SDK with Gemini 1.5 Flash (free tier: 15 RPM / 1500 RPD).
"""

import os
from google import genai
from google.genai import types
from PIL import Image
import io


def extract_equation_from_image(image_path: str) -> str:
    """
    Extract a math equation from an image using Gemini Vision.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    client = genai.Client(api_key=api_key)

    # Load image and convert to bytes
    image = Image.open(image_path).convert("RGB")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            (
                "Extract the mathematical equation from this image. "
                "Return ONLY the equation as plain text, nothing else. "
                "Use standard ASCII: ^ for exponents (x^2), * for multiplication. "
                "Example output: x^2 - 13x + 42 = 0"
            ),
        ],
    )

    return response.text.strip()
