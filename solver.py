"""
solver.py — Parse OCR text and solve mathematical equations with SymPy.

Handles:
  - Linear equations:      2x + 5 = 15       →  x = 5
  - Quadratic equations:   3x² + 5x - 2 = 0  →  x = 1/3, x = -2
  - Pure expressions:      2 + 3 * 4          →  14
  - Multi-variable (basic): x + y = 10        →  [x = 10 - y]
"""

from typing import Union
import sympy as sp
from parser import parse_expression


def solve_equation(raw_text: str) -> str:
    """
    Main entry point: take raw OCR text, parse it, and solve it.

    Args:
        raw_text: The equation string as extracted (and lightly cleaned) by OCR.

    Returns:
        A human-readable string describing the solution or simplified result.

    Raises:
        ValueError: If parsing or solving fails in a recoverable way.
    """
    # 1. Parse the raw OCR text into a SymPy-compatible string
    try:
        expr_str = parse_expression(raw_text)
    except ValueError as e:
        raise ValueError(f"Parsing failed: {e}") from e

    # 2. Detect free symbols and decide how to handle the expression
    try:
        sympy_expr = sp.sympify(expr_str, evaluate=False)
    except (sp.SympifyError, SyntaxError, TypeError) as e:
        raise ValueError(
            f"Could not interpret the expression '{expr_str}'. "
            "Please ensure the image shows a clear mathematical equation."
        ) from e

    free_symbols = sympy_expr.free_symbols

    # 3a. No variables → evaluate numerically
    if not free_symbols:
        return _evaluate_numeric(sympy_expr)

    # 3b. One or more variables → solve symbolically
    return _solve_symbolic(sympy_expr, free_symbols, raw_text)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _evaluate_numeric(expr: sp.Expr) -> str:
    """Evaluate a constant expression and return a clean string."""
    try:
        result = sp.simplify(expr)
        numeric = float(result.evalf())
        # Show as integer if it's whole
        if numeric == int(numeric):
            return f"= {int(numeric)}"
        return f"≈ {numeric:.4f}"
    except Exception as e:
        raise ValueError(f"Could not evaluate the expression: {e}") from e


def _solve_symbolic(
    expr: sp.Expr,
    free_symbols: set,
    original_text: str,
) -> str:
    """
    Attempt to solve a symbolic expression for its variable(s).

    Strategy:
      - If there is one variable, try sp.solve() then sp.solveset().
      - If there are multiple variables, return a simplified/rearranged form.
    """
    if len(free_symbols) == 1:
        var = next(iter(free_symbols))
        return _solve_single_variable(expr, var)
    else:
        return _solve_multivariable(expr, free_symbols)


def _solve_single_variable(expr: sp.Expr, var: sp.Symbol) -> str:
    """Solve a single-variable equation and format the result."""
    try:
        solutions = sp.solve(expr, var)
    except NotImplementedError:
        solutions = []

    # Fallback: solveset (handles more cases, e.g., periodic)
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
        # Try numerical solving as a last resort
        return _numerical_fallback(expr, var)

    return _format_solutions(var, solutions)


def _solve_multivariable(expr: sp.Expr, free_symbols: set) -> str:
    """
    For multi-variable expressions, simplify and return the expression.
    Full multi-equation systems require multiple equations, so we just
    return the simplified form here.
    """
    simplified = sp.simplify(expr)
    vars_str = ", ".join(str(s) for s in sorted(free_symbols, key=str))
    return f"Simplified expression (variables: {vars_str}):\n{simplified} = 0"


def _numerical_fallback(expr: sp.Expr, var: sp.Symbol) -> str:
    """Use SymPy's nsolve to find a numerical root near x=0 or x=1."""
    for start in [0, 1, -1, 2, 10]:
        try:
            root = sp.nsolve(expr, var, start)
            root_rounded = round(float(root), 4)
            return f"{var} ≈ {root_rounded}  (numerical solution)"
        except Exception:
            continue
    raise ValueError(
        "Could not find a solution. "
        "The equation may have no real solutions or may be unsupported."
    )


def _format_solutions(var: sp.Symbol, solutions: list) -> str:
    """Format a list of SymPy solutions into a readable string."""
    parts = []
    for sol in solutions:
        try:
            # Try to get a clean float
            numeric = float(sol.evalf())
            if numeric == int(numeric):
                parts.append(f"{var} = {int(numeric)}")
            else:
                # Show exact form AND decimal approximation
                exact = str(sol)
                approx = round(numeric, 4)
                if exact != str(approx):
                    parts.append(f"{var} = {exact}  (≈ {approx})")
                else:
                    parts.append(f"{var} = {approx}")
        except (TypeError, ValueError):
            # Solution is complex or symbolic — show as-is
            parts.append(f"{var} = {sol}")

    return "\n".join(parts)
