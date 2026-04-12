# MathLens — Offline Math Equation Solver

Upload an image of a handwritten or printed mathematical equation and get the solution instantly.
The entire pipeline runs locally (or on your server) — no external AI APIs required.

```
Image → OCR (Tesseract) → Parser → SymPy Solver → Result
```

---

## Features

- **Image upload** with drag-and-drop support
- **OpenCV preprocessing** — grayscale, adaptive threshold, denoising
- **Tesseract OCR** — extracts the equation as text
- **Smart parser** — converts `2x + 5 = 15` to valid SymPy syntax
- **SymPy solver** — solves linear, quadratic, and polynomial equations
- **Clean dark UI** — works on desktop and mobile

---

## Project Structure

```
math-solver-ai/
├── app.py              # Flask server & routing
├── solver.py           # SymPy equation solving
├── ocr.py              # OpenCV preprocessing + Tesseract OCR
├── parser.py           # OCR text → SymPy expression conversion
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Frontend HTML
├── static/
│   ├── style.css       # Styling
│   └── script.js       # Frontend JS
├── uploads/            # Temporary upload folder (auto-created)
└── README.md
```

---

## Prerequisites

### 1. Python 3.9+

Download from https://python.org

### 2. Tesseract OCR engine

Tesseract must be installed on your system separately from the Python package.

**macOS (Homebrew):**
```bash
brew install tesseract
```

**Ubuntu / Debian:**
```bash
sudo apt-get update && sudo apt-get install -y tesseract-ocr
```

**Windows:**
- Download the installer from https://github.com/UB-Mannheim/tesseract/wiki
- Default install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- If pytesseract cannot find it automatically, add this line in `ocr.py`:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
  ```

Verify installation:
```bash
tesseract --version
```

---

## Local Setup

```bash
# 1. Clone or download the project
git clone https://github.com/your-username/math-solver-ai.git
cd math-solver-ai

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Run the Flask development server
python app.py
```

Open your browser at **http://localhost:5000**

---

## Environment Variables

| Variable       | Default | Description                          |
|----------------|---------|--------------------------------------|
| `PORT`         | `5000`  | Port the Flask server listens on     |
| `FLASK_DEBUG`  | `false` | Set to `true` for hot-reload in dev  |

Example:
```bash
PORT=8080 FLASK_DEBUG=true python app.py
```

---

## Usage

1. Open the app in your browser.
2. Click **"browse files"** or drag an image onto the drop zone.
3. Preview your equation image.
4. Click **"Solve Equation"**.
5. See the detected equation and its solution.

### Tips for best OCR results

- Use **clear, high-contrast** images (dark text on white paper works best).
- Avoid shadows or glare.
- Crop the image to show only the equation.
- Printed equations are more reliable than handwriting.

### Supported equation types

| Input image text      | Solution output              |
|-----------------------|------------------------------|
| `2x + 5 = 15`         | `x = 5`                      |
| `3x² + 5x - 2 = 0`    | `x = 1/3  (≈ 0.3333)`<br>`x = -2` |
| `x² - 9 = 0`          | `x = 3`, `x = -3`            |
| `2 + 3 * 4`           | `= 14`                       |

---

## Deploying to Render

Render is a free cloud platform that works well for Flask apps.

### Steps

1. **Push your project to GitHub.**

2. **Go to [render.com](https://render.com)** and create a free account.

3. Click **New → Web Service**, connect your GitHub repo.

4. Configure the service:
   - **Environment:** Python 3
   - **Build Command:**
     ```
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```
     gunicorn app:app --bind 0.0.0.0:$PORT
     ```

5. **Add Tesseract** — Render's default Python image does not include Tesseract.
   Create a file called `render.yaml` in the project root:

   ```yaml
   services:
     - type: web
       name: math-solver-ai
       env: python
       buildCommand: "apt-get install -y tesseract-ocr && pip install -r requirements.txt"
       startCommand: "gunicorn app:app --bind 0.0.0.0:$PORT"
   ```

   Alternatively, add a `build.sh` script:
   ```bash
   #!/usr/bin/env bash
   apt-get install -y tesseract-ocr
   pip install -r requirements.txt
   ```
   And set the build command to `bash build.sh`.

6. Click **Deploy**. Your app will be live at `https://your-app.onrender.com`.

---

## Running Tests (optional)

You can quickly test the parser and solver from the command line:

```python
# test_manual.py
from parser import parse_expression
from solver import solve_equation

tests = [
    "2x + 5 = 15",
    "3x^2 + 5x - 2 = 0",
    "x^2 - 9 = 0",
    "2 + 3 * 4",
]

for t in tests:
    print(f"Input:  {t}")
    print(f"Result: {solve_equation(t)}")
    print()
```

Run with:
```bash
python test_manual.py
```

---

## Tech Stack

| Layer       | Technology                  |
|-------------|-----------------------------|
| Frontend    | HTML · CSS · Vanilla JS     |
| Backend     | Python · Flask              |
| OCR         | Tesseract · pytesseract     |
| Preprocessing | OpenCV · Pillow           |
| Math engine | SymPy                       |
| Production  | Gunicorn                    |

---

## Limitations

- Handwriting recognition accuracy depends on image quality.
- Very complex equations (integrals, matrix systems) are not yet supported.
- OCR may struggle with closely spaced symbols.

---

## License

MIT — free to use and modify.
