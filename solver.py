"""
solver.py — Parse OCR text and solve/evaluate with SymPy.

Handles:
  - Equations:           x**2 - 13*x + 42 = 0  →  x = 6, x = 7
  - Definite integrals:  integrate(4*x**3, (x, 0, 4))  →  256
  - Indefinite integrals: integrate(4*x**3, x)  →  x**4
  - Derivatives:         diff(x**3, x)  →  3*x**2
  - Expressions:         2 + 3*4  →  14
"""

import re
import sympy as sp
from parser import parse_expression


def solve_equation(raw_text: str) -> str:
    """
    Main entry point: take raw OCR text, parse it, and solve/evaluate it.
    """
    text = raw_text.strip()

    # --- Definite integral: integrate(expr, (var, a, b)) ---
    m = re.match(r"integrate\((.+),\s*\((\w+),\s*(.+),\s*(.+)\)\)", text, re.IGNORECASE)
    if m:
        expr_str, var_str, lower, upper = m.group(1), m.group(2), m.group(3), m.group(4)
        try:
            var = sp.Symbol(var_str)
            expr = sp.sympify(expr_str)
            result = sp.integrate(expr, (var, sp.sympify(lower), sp.sympify(upper)))
            result = sp.simplify(result)
            numeric = float(result.evalf())
            if numeric == int(numeric):
                return f"= {int(numeric)}"
            return f"≈ {round(numeric, 4)}"
        except Exception as e:
            raise ValueError(f"Could not evaluate integral: {e}")

    # --- Indefinite integral: integrate(expr, x) ---
    m = re.match(r"integrate\((.+),\s*(\w+)\)", text, re.IGNORECASE)
    if m:
        expr_str, var_str = m.group(1), m.group(2)
        try:
            var = sp.Symbol(var_str)
            expr = sp.sympify(expr_str)
            result = sp.integrate(expr, var)
            return f"= {result} + C"
        except Exception as e:
            raise ValueError(f"Could not evaluate integral: {e}")

    # --- Derivative: diff(expr, x) ---
    m = re.match(r"diff\((.+),\s*(\w+)\)", text, re.IGNORECASE)
    if m:
        expr_str, var_str = m.group(1), m.group(2)
        try:
            var = sp.Symbol(var_str)
            expr = sp.sympify(expr_str)
            result = sp.diff(expr, var)
            return f"= {result}"
        except Exception as e:
            raise ValueError(f"Could not differentiate: {e}")

    # --- Equation or expression (existing logic) ---
    try:
        expr_str = parse_expression(text)
    except ValueError as e:
        raise ValueError(f"Parsing failed: {e}")

    try:
        sympy_expr = sp.sympify(expr_str, evaluate=False)
    except Exception as e:
        raise ValueError(f"Could not interpret '{expr_str}': {e}")

    free_symbols = sympy_expr.free_symbols

    if not free_symbols:
        return _evaluate_numeric(sympy_expr)

    if len(free_symbols) == 1:
        var = next(iter(free_symbols))
        return _solve_single_variable(sympy_expr, var)

    simplified = sp.simplify(sympy_expr)
    vars_str = ", ".join(str(s) for s in sorted(free_symbols, key=str))
    return f"Simplified (variables: {vars_str}):\n{simplified} = 0"


def _evaluate_numeric(expr):
    result = sp.simplify(expr)
    numeric = float(result.evalf())
    if numeric == int(numeric):
        return f"= {int(numeric)}"
    return f"≈ {round(numeric, 4)}"


def _solve_single_variable(expr, var):
    try:
        solutions = sp.solve(expr, var)
    except NotImplementedError:
        solutions = []

    if not solutions:
        try:
            sol_set = sp.solveset(expr, var, domain=sp.S.Reals)
            if sol_set.is_FiniteSet:
                solutions = list(sol_set)
            elif not sol_set.is_empty:
                return f"{var} ∈ {sol_set}"
        except Exception:
            pass

    if not solutions:
        for start in [0, 1, -1, 2, 10]:
            try:
                root = sp.nsolve(expr, var, start)
                return f"{var} ≈ {round(float(root), 4)}  (numerical)"
            except Exception:
                continue
        raise ValueError("No real solution found.")

    parts = []
    for sol in solutions:
        try:
            numeric = float(sol.evalf())
            exact = str(sol)
            approx = round(numeric, 4)
            if numeric == int(numeric):
                parts.append(f"{var} = {int(numeric)}")
            elif exact != str(approx):
                parts.append(f"{var} = {exact}  (≈ {approx})")
            else:
                parts.append(f"{var} = {approx}")
        except (TypeError, ValueError):
            parts.append(f"{var} = {sol}")

    return "\n".join(parts)
