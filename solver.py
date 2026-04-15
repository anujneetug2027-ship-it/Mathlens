"""
solver.py — Solve math expressions with SymPy and return step-by-step results.

Gemini is used ONLY for OCR (image → text).
All solving is done offline by SymPy.

Returns a list of step dicts:
  [{"title": "...", "expr": "...", "type": "step|final"}, ...]
"""

import re
import sympy as sp
from parser import parse_expression


def solve_equation(raw_text: str) -> list:
    """
    Parse and solve raw equation text. Returns list of step dicts.
    """
    text = raw_text.strip()
    steps = []

    steps.append({"title": "Input received", "expr": text, "type": "step"})

    # --- Definite integral: integrate(expr, (var, a, b)) ---
    m = re.match(r"integrate\((.+),\s*\((\w+),\s*(.+?),\s*(.+?)\)\)\s*$", text, re.IGNORECASE)
    if m:
        expr_str, var_str, lower, upper = m.group(1), m.group(2), m.group(3), m.group(4)
        var = sp.Symbol(var_str)
        expr = sp.sympify(expr_str)
        steps.append({"title": "Identified as definite integral", "expr": f"∫({expr_str}) d{var_str} from {lower} to {upper}", "type": "step"})
        antideriv = sp.integrate(expr, var)
        steps.append({"title": "Antiderivative found", "expr": f"F({var_str}) = {antideriv}", "type": "step"})
        result = sp.integrate(expr, (var, sp.sympify(lower), sp.sympify(upper)))
        result = sp.simplify(result)
        numeric = float(result.evalf())
        answer = int(numeric) if numeric == int(numeric) else round(numeric, 6)
        steps.append({"title": f"Evaluate F({upper}) - F({lower})", "expr": f"{antideriv.subs(var, sp.sympify(upper))} - {antideriv.subs(var, sp.sympify(lower))}", "type": "step"})
        steps.append({"title": "Final Answer", "expr": str(answer), "type": "final"})
        return steps

    # --- Indefinite integral: integrate(expr, var) ---
    m = re.match(r"integrate\((.+),\s*(\w+)\)\s*$", text, re.IGNORECASE)
    if m:
        expr_str, var_str = m.group(1), m.group(2)
        var = sp.Symbol(var_str)
        expr = sp.sympify(expr_str)
        steps.append({"title": "Identified as indefinite integral", "expr": f"∫({expr_str}) d{var_str}", "type": "step"})
        result = sp.integrate(expr, var)
        steps.append({"title": "Apply integration rules", "expr": str(result), "type": "step"})
        steps.append({"title": "Final Answer (+ C for constant)", "expr": f"{result} + C", "type": "final"})
        return steps

    # --- Derivative: diff(expr, var) ---
    m = re.match(r"diff\((.+),\s*(\w+)\)\s*$", text, re.IGNORECASE)
    if m:
        expr_str, var_str = m.group(1), m.group(2)
        var = sp.Symbol(var_str)
        expr = sp.sympify(expr_str)
        steps.append({"title": "Identified as derivative", "expr": f"d/d{var_str} [{expr_str}]", "type": "step"})
        result = sp.diff(expr, var)
        simplified = sp.simplify(result)
        steps.append({"title": "Apply differentiation rules", "expr": str(result), "type": "step"})
        if str(result) != str(simplified):
            steps.append({"title": "Simplified", "expr": str(simplified), "type": "step"})
        steps.append({"title": "Final Answer", "expr": str(simplified), "type": "final"})
        return steps

    # --- Equation or arithmetic expression ---
    try:
        expr_str = parse_expression(text)
    except ValueError as e:
        raise ValueError(f"Could not parse: {e}")

    steps.append({"title": "Parsed expression", "expr": expr_str, "type": "step"})

    try:
        sympy_expr = sp.sympify(expr_str, evaluate=False)
    except Exception as e:
        raise ValueError(f"Could not interpret expression: {e}")

    free_symbols = sympy_expr.free_symbols

    # Pure arithmetic — no variables
    if not free_symbols:
        evaluated = sp.simplify(sympy_expr)
        numeric = float(evaluated.evalf())
        answer = int(numeric) if numeric == int(numeric) else round(numeric, 6)
        steps.append({"title": "Evaluate arithmetic", "expr": str(evaluated), "type": "step"})
        steps.append({"title": "Final Answer", "expr": str(answer), "type": "final"})
        return steps

    # Single variable — solve
    if len(free_symbols) == 1:
        var = next(iter(free_symbols))
        steps.append({"title": f"Solve for {var}", "expr": f"{expr_str} = 0", "type": "step"})

        try:
            solutions = sp.solve(sympy_expr, var)
        except NotImplementedError:
            solutions = []

        if not solutions:
            try:
                sol_set = sp.solveset(sympy_expr, var, domain=sp.S.Reals)
                if sol_set.is_FiniteSet:
                    solutions = list(sol_set)
            except Exception:
                pass

        if not solutions:
            for start in [0, 1, -1, 2, 10]:
                try:
                    root = sp.nsolve(sympy_expr, var, start)
                    steps.append({"title": "Numerical method used", "expr": f"{var} ≈ {round(float(root), 4)}", "type": "step"})
                    steps.append({"title": "Final Answer", "expr": f"{var} ≈ {round(float(root), 4)}", "type": "final"})
                    return steps
                except Exception:
                    continue
            raise ValueError("No real solution found.")

        steps.append({"title": "Factor / apply quadratic formula", "expr": f"{len(solutions)} solution(s) found", "type": "step"})

        answer_parts = []
        for sol in solutions:
            try:
                numeric = float(sol.evalf())
                exact = str(sol)
                approx = round(numeric, 4)
                if numeric == int(numeric):
                    answer_parts.append(f"{var} = {int(numeric)}")
                    steps.append({"title": f"Solution", "expr": f"{var} = {int(numeric)}", "type": "step"})
                else:
                    answer_parts.append(f"{var} = {exact} ≈ {approx}")
                    steps.append({"title": f"Solution (exact)", "expr": f"{var} = {exact}", "type": "step"})
                    steps.append({"title": f"Solution (decimal)", "expr": f"{var} ≈ {approx}", "type": "step"})
            except Exception:
                answer_parts.append(f"{var} = {sol}")
                steps.append({"title": "Solution", "expr": f"{var} = {sol}", "type": "step"})

        steps.append({"title": "Final Answer", "expr": "  ,  ".join(answer_parts), "type": "final"})
        return steps

    # Multiple variables
    simplified = sp.simplify(sympy_expr)
    vars_str = ", ".join(str(s) for s in sorted(free_symbols, key=str))
    steps.append({"title": f"Multiple variables ({vars_str}) — simplified form", "expr": str(simplified), "type": "step"})
    steps.append({"title": "Final Answer", "expr": f"{simplified} = 0", "type": "final"})
    return steps
