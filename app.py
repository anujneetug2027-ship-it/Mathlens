import os
import uuid
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from ocr import extract_equation_from_image
from solver import solve_equation

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    """Serve the main HTML page."""
    return render_template("index.html")


@app.route("/solve", methods=["POST"])
def solve():
    """
    Handle image upload, run OCR, parse and solve the equation.
    Returns JSON with detected equation and solution.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Please upload a PNG, JPG, or similar image."}), 400

    # Save the uploaded file with a unique name to avoid collisions
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(unique_filename))
    file.save(filepath)

    try:
        # Step 1: OCR — extract raw equation text from the image
        raw_text = extract_equation_from_image(filepath)

        if not raw_text:
            return jsonify({"error": "Could not detect any text in the image. Try a clearer photo."}), 422

        # Step 2: Solve — parse and solve the equation
        result = solve_equation(raw_text)

        return jsonify({
            "detected_equation": raw_text,
            "result": result,
        })

    except Exception as e:
        return jsonify({"error": f"An error occurred while processing: {str(e)}"}), 500

    finally:
        # Clean up uploaded file after processing
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
