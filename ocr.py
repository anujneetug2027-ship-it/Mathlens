"""
ocr.py — OCR via Gemini 2.5 Flash REST API (no SDK, no extra packages).

Flow:
  1. Image → base64 encode
  2. POST to Gemini REST API → get equation text back
  3. Return text to solver.py → SymPy solves it locally

Gemini only reads the image. All math solving is done by SymPy on the server.
"""

import os
import base64
import json
import urllib.request
import urllib.error
from PIL import Image
import io


def extract_equation_from_image(image_path: str) -> str:
    """
    Extract a math equation from an image using Gemini 2.5 Flash vision.

    Args:
        image_path: Path to the uploaded image file.

    Returns:
        The detected equation as a plain text string.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    # Convert image to JPEG bytes and base64 encode
    image = Image.open(image_path).convert("RGB")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # Build the REST request (same format your local HTML uses)
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )

    payload = {
        "contents": [{
            "parts": [
                {
                    "text": (
                        "Extract the mathematical equation from this image. "
                        "Return ONLY the equation as plain text, nothing else. "
                        "Use standard ASCII: ^ for exponents (x^2), "
                        "* for multiplication. "
                        "Example output: x^2 - 13x + 42 = 0"
                    )
                },
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_b64
                    }
                }
            ]
        }]
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Gemini API error {e.code}: {error_body}")

    return result["candidates"][0]["content"]["parts"][0]["text"].strip()
