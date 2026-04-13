"""
ocr.py — OCR via Gemini 2.5 Flash REST API.
"""

import os
import base64
import json
import urllib.request
import urllib.error
from PIL import Image
import io


def extract_equation_from_image(image_path: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    image = Image.open(image_path).convert("RGB")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )

    payload = {
        "contents": [{
            "parts": [
                {
                    "text": (
                        "Extract the mathematical expression from this image. "
                        "Return ONLY the expression as plain text, nothing else. "
                        "Use these exact formats:\n"
                        "- Exponents: x^2 means x**2\n"
                        "- Multiplication: write 4*x not 4x\n"
                        "- Definite integral: integrate(4*x**3, (x, 0, 4))\n"
                        "- Indefinite integral: integrate(4*x**3, x)\n"
                        "- Equation: x**2 - 13*x + 42 = 0\n"
                        "Return ONLY the expression, no explanation."
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
