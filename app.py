import os
import uuid
import subprocess
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

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


@app.route("/debug")
def debug():
    """Shows environment info to diagnose Tesseract issues."""
    info = {}

    # Find tesseract
    for path in ["/usr/bin/tesseract", "/usr/local/bin/tesseract"]:
        info[f"exists_{path}"] = os.path.isfile(path)

    try:
        result = subprocess.run(["which", "tesseract"], capture_output=True, text=True)
        info["which_tesseract"] = result.stdout.strip() or "not found"
    except Exception as e:
        info["which_tesseract"] = str(e)

    try:
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        info["tesseract_version"] = result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        info["tesseract_version"] = str(e)

    try:
        import pytesseract
        info["pytesseract_cmd"] = pytesseract.pytesseract.tesseract_cmd
        info["pytesseract_version"] = pytesseract.get_tesseract_version()
    except Exception as e:
        info["pytesseract_error"] = str(e)

    return jsonify(info)


@app.route("/solve", methods=["POST"])
def solve():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type."}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(unique_filename))
    file.save(filepath)

    try:
        from ocr import extract_equation_from_image
        from solver import solve_equation

        raw_text = extract_equation_from_image(filepath)
        if not raw_text:
            return jsonify({"error": "Could not detect any text. Try a clearer image."}), 422

        result = solve_equation(raw_text)
        return jsonify({"detected_equation": raw_text, "result": result})

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
