"""
Mock Solver for testing pipeline without heavy LLM
Generates simple code based on problem patterns
"""

import re

class MockLLMClient:
    """Mock LLM that generates simple code based on problem keywords"""
    
    def __init__(self):
        print("Mock LLM initialized (no model loading required)")
    
    def generate(self, prompt: str) -> str:
        """Generate simple code based on problem patterns"""
        
        # Extract problem from prompt
        problem_match = re.search(r"Problem: (.+?)(?:Code:|$)", prompt, re.DOTALL)
        problem = problem_match.group(1).strip() if problem_match else ""
        
        # Pattern matching for common problems
        if "+" in problem and any(c.isdigit() for c in problem):
            # Simple addition
            numbers = re.findall(r'\d+', problem)
            if len(numbers) >= 2:
                return f"print({numbers[0]} + {numbers[1]})"
        
        if "sum" in problem.lower() or "total" in problem.lower():
            # Sum problems
            numbers = re.findall(r'\d+', problem)
            if numbers:
                return f"print(sum([{', '.join(numbers)}]))"
        
        if "product" in problem.lower() or "*" in problem or "×" in problem:
            # Multiplication
            numbers = re.findall(r'\d+', problem)
            if len(numbers) >= 2:
                return f"print({numbers[0]} * {numbers[1]})"
        
        if "square" in problem.lower():
            # Square
            numbers = re.findall(r'\d+', problem)
            if numbers:
                return f"print({numbers[0]} ** 2)"
        
        if "range" in problem.lower() or "interval" in problem.lower():
            # Range/interval problems
            return "print('[0, 1/2]')"
        
        if any(word in problem.lower() for word in ["solve", "equation", "find", "calculate"]):
            # Generic math problem - try sympy
            return """from sympy import symbols, solve, simplify
x, a = symbols('x a')
result = solve(x**2 - 2*x + 1, x)
print(result[0] if result else 'No solution')"""
        
        # Default fallback
        return "print('42')"

class MockSolver:
    """Mock solver using pattern-based code generation"""
    
    def __init__(self):
        self.llm = MockLLMClient()
    
    def generate_code(self, problem_text: str, strategy: str) -> str:
        """Generate code based on problem pattern"""
        
        # Simple prompt
        prompt = f"Solve this problem:\nProblem: {problem_text}\nCode:"
        
        # Get mock response
        code = self.llm.generate(prompt)
        
        # Basic validation
        if not code.strip():
            code = "print('No solution')"
        
        return code
