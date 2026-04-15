import os
import uuid
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from ocr import extract_equation_from_image   # Gemini — OCR only
from solver import solve_equation              # SymPy — fully offline

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


# ── Image route: Gemini OCR → SymPy solver ──────────────────────────────────
@app.route("/solve", methods=["POST"])
def solve():
    if "image" not in request.files:
        return jsonify({"error": "No image provided."}), 400
    file = request.files["image"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file."}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(f"{uuid.uuid4().hex}.{ext}"))
    file.save(filepath)

    try:
        # Gemini used ONLY here for OCR
        raw_text = extract_equation_from_image(filepath)
        if not raw_text:
            return jsonify({"error": "No text detected. Try a clearer image."}), 422

        # SymPy solves — no internet needed
        steps = solve_equation(raw_text)
        return jsonify({"detected_equation": raw_text, "steps": steps})

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


# ── Text route: no OCR, pure SymPy offline ──────────────────────────────────
@app.route("/solve_text", methods=["POST"])
def solve_text():
    data = request.get_json()
    if not data or not data.get("equation", "").strip():
        return jsonify({"error": "No equation provided."}), 400

    raw_text = data["equation"].strip()

    try:
        # 100% offline — SymPy only
        steps = solve_equation(raw_text)
        return jsonify({"detected_equation": raw_text, "steps": steps})
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
