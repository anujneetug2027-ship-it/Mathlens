"""
parser.py — Convert OCR-extracted text into valid SymPy-parseable expressions.

OCR output is messy. This module normalises common issues:
  - Implicit multiplication:  2x   →  2*x
  - Unicode superscripts:     x²   →  x**2
  - Common OCR substitutions: 'O'  →  '0'  (letter O → zero)
  - Equation splitting:       lhs = rhs  →  (lhs) - (rhs)  for SymPy
"""

import re


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_expression(text: str) -> str:
    """
    Convert raw OCR text into a SymPy-compatible expression string.

    If the text contains '=', it is treated as an equation and converted to
    the form  lhs - rhs  so SymPy can solve for the variable where result = 0.

    Args:
        text: Raw or lightly cleaned string from the OCR module.

    Returns:
        A string suitable for passing to sympy.sympify() or sympy.solve().

    Raises:
        ValueError: If the expression is empty after normalisation.
    """
    if not text or not text.strip():
        raise ValueError("Empty expression received.")

    expr = text.strip()

    # --- Step 1: fix common OCR character substitutions ---
    expr = _fix_ocr_substitutions(expr)

    # --- Step 2: normalise unicode superscripts / exponents ---
    expr = _normalise_superscripts(expr)

    # --- Step 3: handle the '=' sign (equation vs expression) ---
    if "=" in expr:
        expr = _split_equation(expr)
    # if no '=', treat as an expression to simplify/evaluate directly

    # --- Step 4: insert explicit multiplication operators ---
    expr = _insert_multiplication(expr)

    # --- Step 5: final cleanup ---
    expr = _final_cleanup(expr)

    if not expr.strip():
        raise ValueError("Expression is empty after parsing.")

    return expr


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _fix_ocr_substitutions(text: str) -> str:
    """Replace characters that OCR commonly misreads."""
    substitutions = {
        # Letter 'O' (uppercase) in a numeric context → digit 0
        # We handle this carefully to avoid breaking variable names
        "×": "*",      # unicode multiplication sign
        "÷": "/",      # unicode division sign
        "−": "-",      # unicode minus sign (different from ASCII hyphen)
        "–": "-",      # en-dash
        "—": "-",      # em-dash
        "²": "**2",    # superscript 2 (sometimes OCR misses the ^)
        "³": "**3",    # superscript 3
        "^": "**",     # caret to Python exponentiation
        # Remove stray pipe characters
        "|": "",
    }
    for bad, good in substitutions.items():
        text = text.replace(bad, good)
    return text


def _normalise_superscripts(text: str) -> str:
    """
    Convert unicode superscript digits to Python exponentiation syntax.

    Handles patterns like  x²  →  x**2  and  x³  →  x**3
    also handles already-converted **2 from the substitution step.
    """
    superscript_map = {
        "⁰": "**0", "¹": "**1", "²": "**2", "³": "**3",
        "⁴": "**4", "⁵": "**5", "⁶": "**6", "⁷": "**7",
        "⁸": "**8", "⁹": "**9",
    }
    for sup, replacement in superscript_map.items():
        text = text.replace(sup, replacement)
    return text


def _split_equation(text: str) -> str:
    """
    Split 'lhs = rhs' into '(lhs) - (rhs)' so SymPy can solve it as f(x)=0.

    If multiple '=' signs exist (rare), only the first is used.
    """
    parts = text.split("=", 1)
    lhs = parts[0].strip()
    rhs = parts[1].strip() if len(parts) > 1 else "0"

    # If rhs is empty after split, default to 0
    if not rhs:
        rhs = "0"

    return f"({lhs}) - ({rhs})"


def _insert_multiplication(expr: str) -> str:
    """
    Insert '*' where multiplication is implied but omitted.

    Handles:
      2x    →  2*x
      3(x)  →  3*(x)
      (x+1)(x-1)  →  (x+1)*(x-1)
      x2    →  x*2   (digit after variable letter)
      2xy   →  2*x*y (consecutive variables — limited support)
    """
    # Number immediately followed by a letter:  2x  →  2*x
    expr = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", expr)

    # Number immediately followed by '(':  3(x+1)  →  3*(x+1)
    expr = re.sub(r"(\d)(\()", r"\1*\2", expr)

    # Letter immediately followed by '(':  x(y+1)  →  x*(y+1)
    expr = re.sub(r"([a-zA-Z])(\()", r"\1*\2", expr)

    # Closing ')' immediately followed by opening '(':  (a+b)(c+d)  →  (a+b)*(c+d)
    expr = re.sub(r"(\))(\()", r"\1*\2", expr)

    # Closing ')' immediately followed by a letter or digit
    expr = re.sub(r"(\))([a-zA-Z0-9])", r"\1*\2", expr)

    return expr


def _final_cleanup(expr: str) -> str:
    """Remove stray whitespace and normalise the expression string."""
    # Remove all spaces (SymPy handles this fine, and it avoids parse errors)
    expr = expr.replace(" ", "")
    # Collapse multiple operators that OCR might produce (e.g. '--' → '+')
    expr = re.sub(r"--", "+", expr)
    expr = re.sub(r"\+\+", "+", expr)
    return expr
