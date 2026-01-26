from sympy import *

def solve():
    x = symbols('x')
    eq = x**4 - 4*x**2 + 3
    solutions = solve(eq, x)
    # Convert to LaTeX
    latex_solutions = [latex(sol) for sol in solutions]
    return r"\boxed{" + ", ".join(latex_solutions) + "}"

if __name__ == "__main__":
    result = solve()
    print(result)
