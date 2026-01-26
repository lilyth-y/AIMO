"""
Reverse Engineering Data Generator
- Generates high-quality math problems with known integer solutions.
- Uses 'Round-Trip Verification' to ensure solvability.
- Focuses on AIMO-style problems (Answer: 0-99999).
"""

import random
import sympy
from sympy import symbols, Eq, solve, diophantine
from typing import Dict, Any, Optional, Tuple

class ProblemGenerator:
    def __init__(self):
        self.verified_count = 0

    def generate(self) -> Optional[Dict[str, Any]]:
        """
        Generates a single verified problem.
        Returns dict with 'problem', 'answer', 'domain', 'type'.
        """
        # Weighted choice to favor harder problems
        choices = ['Algebra', 'Number Theory', 'Polynomials', 'Sequences']
        weights = [0.2, 0.2, 0.3, 0.3]  # More weight on new hard types
        domain = random.choices(choices, weights=weights, k=1)[0]
        
        if domain == 'Algebra':
            return self._generate_algebra()
        elif domain == 'Number Theory':
            return self._generate_number_theory()
        elif domain == 'Polynomials':
            return self._generate_polynomial_vieta()
        elif domain == 'Sequences':
            return self._generate_sequence()
        
        return None

    def _generate_algebra(self) -> Optional[Dict[str, Any]]:
        """
        Generates Algebra problems (Linear/Quadratic Equations).
        """
        # 1. Pick a random integer answer (0-100 to keep coefficients small)
        x_val = random.randint(0, 100)
        
        # 2. Create a linear equation: ax + b = c
        a = random.randint(2, 10)
        b = random.randint(1, 50)
        c = a * x_val + b
        
        problem_text = f"Find the integer $x$ such that ${a}x + {b} = {c}$."
        
        # 3. Round-Trip Verification
        if self._verify_algebra(a, b, c, x_val):
            return {
                'problem': problem_text,
                'answer': x_val,
                'domain': 'Algebra',
                'type': 'Linear Equation'
            }
        return None

    def _generate_polynomial_vieta(self) -> Optional[Dict[str, Any]]:
        """
        Generates problems solvable by Vieta's formulas.
        Example: Given x^2 + bx + c = 0 with roots alpha, beta, find alpha^2 + beta^2.
        """
        # 1. Choose integer roots
        r1 = random.randint(-10, 10)
        r2 = random.randint(-10, 10)
        
        # 2. Construct coefficients: x^2 - (r1+r2)x + r1*r2 = 0
        b_coeff = -(r1 + r2)
        c_coeff = r1 * r2
        
        # 3. Define the target expression: alpha^2 + beta^2
        # Value = (r1+r2)^2 - 2*r1*r2 = b^2 - 2c
        target_val = r1**2 + r2**2
        
        # Format equation string properly (handle signs)
        sign_b = "+" if b_coeff >= 0 else ""
        sign_c = "+" if c_coeff >= 0 else ""
        eq_str = f"x^2 {sign_b} {b_coeff}x {sign_c} {c_coeff} = 0"
        
        problem_text = (
            f"Let $\\alpha$ and $\\beta$ be the roots of the quadratic equation "
            f"${eq_str}$. Calculate the value of $\\alpha^2 + \\beta^2$."
        )
        
        return {
            'problem': problem_text,
            'answer': target_val,
            'domain': 'Algebra',
            'type': 'Polynomial Vieta'
        }

    def _generate_sequence(self) -> Optional[Dict[str, Any]]:
        """
        Generates recursive sequence problems.
        a_n = p * a_{n-1} + q
        """
        # 1. Define recurrence parameters
        p = random.randint(2, 5)
        q = random.randint(1, 10)
        a1 = random.randint(1, 5)
        
        # 2. Calculate target term (e.g., 5th to 8th term to keep numbers manageable but requiring logic)
        n_target = random.randint(5, 8)
        
        current = a1
        for _ in range(n_target - 1):
            current = p * current + q
            
        problem_text = (
            f"A sequence is defined by $a_1 = {a1}$ and $a_n = {p}a_{{n-1}} + {q}$ for $n > 1$. "
            f"Find the value of $a_{{{n_target}}}$."
        )
        
        return {
            'problem': problem_text,
            'answer': current,
            'domain': 'Sequences',
            'type': 'Linear Recurrence'
        }

    def _generate_number_theory(self) -> Optional[Dict[str, Any]]:
        """
        Generates Number Theory problems (Diophantine/Modular/CRT).
        """
        rand_val = random.random()
        if rand_val < 0.4:
            return self._generate_diophantine()
        elif rand_val < 0.7:
            return self._generate_modular()
        else:
            return self._generate_crt()

    def _generate_crt(self) -> Optional[Dict[str, Any]]:
        """
        Generates Chinese Remainder Theorem problems.
        Find smallest x > 0 such that x = a (mod m) and x = b (mod n).
        """
        # 1. Pick coprime moduli
        primes = [3, 5, 7, 11, 13, 17]
        m = random.choice(primes)
        primes.remove(m)
        n = random.choice(primes)
        
        # 2. Pick target answer
        limit = m * n
        target = random.randint(1, limit - 1)
        
        rem_m = target % m
        rem_n = target % n
        
        problem_text = (
            f"Find the smallest positive integer $x$ such that $x \\equiv {rem_m} \\pmod{{{m}}}$ "
            f"and $x \\equiv {rem_n} \\pmod{{{n}}}$."
        )
        
        return {
            'problem': problem_text,
            'answer': target,
            'domain': 'Number Theory',
            'type': 'CRT'
        }

    def _generate_modular(self) -> Optional[Dict[str, Any]]:
        # Simple Modular Arithmetic: Find x such that x = a (mod m)
        # To make it a problem: "What is the remainder when N is divided by m?"
        # Construct N as a large number expression.
        
        base = random.randint(2, 10)
        exp = random.randint(10, 50)
        m = random.randint(10, 100)
        
        # Calculate answer
        answer = pow(base, exp, m)
        
        problem_text = f"What is the remainder when ${base}^{{{exp}}}$ is divided by ${m}$?"
        
        return {
            'problem': problem_text,
            'answer': answer,
            'domain': 'Number Theory',
            'type': 'Modular Arithmetic'
        }

    def _generate_diophantine(self) -> Optional[Dict[str, Any]]:
        """
        Generates a linear Diophantine equation problem from a target answer.
        ax + by = c
        Includes Round-Trip Verification to ensure uniqueness.
        """
        # 1. Target Answer
        x_target = random.randint(1, 100)
        y_target = random.randint(1, 100)
        
        # 2. Random Coefficients
        a = random.randint(2, 20)
        b = random.randint(2, 20)
        
        # 3. Calculate c
        c = a * x_target + b * y_target
        
        # 4. Verification (Round-Trip)
        # Check if (x_target, y_target) is the UNIQUE positive integer solution
        if self._verify_unique_positive_solution(a, b, c):
            problem_text = f"Find positive integers $x$ and $y$ such that ${a}x + {b}y = {c}$. What is the value of $x$?"
            return {
                "problem": problem_text,
                "answer": x_target,
                "domain": "Number Theory",
                "type": "Diophantine"
            }
        return None

    def _verify_algebra(self, a, b, c, expected_x) -> bool:
        """
        Verifies linear equation ax + b = c has unique solution x.
        """
        x = symbols('x')
        sol = solve(a*x + b - c, x)
        return len(sol) == 1 and sol[0] == expected_x

    def _verify_unique_positive_solution(self, a, b, c):
        """
        Checks if ax + by = c has exactly one positive integer solution.
        """
        # Brute force check for range [1, c/a]
        limit_x = c // a + 1
        count = 0
        for i in range(1, limit_x + 1):
            if (c - a * i) % b == 0:
                j = (c - a * i) // b
                if j > 0:
                    count += 1
        return count == 1

if __name__ == "__main__":
    gen = ProblemGenerator()
    print("Generating 5 sample problems...")
    for _ in range(5):
        p = gen.generate()
        if p:
            print(f"[{p['domain']} - {p['type']}] {p['problem']} -> {p['answer']}")

