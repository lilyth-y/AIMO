
import unittest
import math
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.pipeline.stage5_verification import VerificationRouter

try:
    import sympy as sp
except ImportError:
    sp = None

class TestVerificationRouter(unittest.TestCase):
    def setUp(self):
        self.router = VerificationRouter(rel_tol=1e-5, abs_tol=1e-6)

    def test_basic_equality(self):
        # Integer
        self.assertTrue(self.router.verify(10, {'expected': 10}))
        self.assertFalse(self.router.verify(10, {'expected': 5}))
        
        # Float (within tolerance)
        self.assertTrue(self.router.verify(3.14159, {'expected': 3.141592}))
        self.assertFalse(self.router.verify(3.14, {'expected': 3.14159}))

    def test_parsing(self):
        # String parsing
        self.assertTrue(self.router.verify("100", {'expected': 100}))
        self.assertTrue(self.router.verify("3.5", {'expected': 3.5}))
        
        # Caret parsing
        self.assertTrue(self.router.verify("2^3", {'expected': 8}))
        
        # LaTeX parsing
        self.assertTrue(self.router.verify(r"\frac{1}{2}", {'expected': 0.5}))
        self.assertTrue(self.router.verify(r"\sqrt{4}", {'expected': 2}))

    def test_constraints(self):
        # Integer constraint
        self.assertTrue(self.router.verify(5, {'constraints': ['integer']}))
        self.assertTrue(self.router.verify(5.0, {'constraints': ['integer']}))
        self.assertFalse(self.router.verify(5.1, {'constraints': ['integer']}))
        
        # Non-negative constraint
        self.assertTrue(self.router.verify(0, {'constraints': ['non_negative']}))
        self.assertTrue(self.router.verify(5, {'constraints': ['non_negative']}))
        self.assertFalse(self.router.verify(-1, {'constraints': ['non_negative']}))
        
        # Modulo constraint
        self.assertTrue(self.router.verify(50, {'constraints': ['modulo_100']}))
        self.assertFalse(self.router.verify(150, {'constraints': ['modulo_100']}))

    def test_sympy_comparison(self):
        if not sp:
            print("Skipping SymPy tests")
            return
            
        # Symbolic equality
        self.assertTrue(self.router.verify("sqrt(2)", {'expected': 1.41421356}))
        self.assertTrue(self.router.verify("1/3", {'expected': 0.33333333}))
        
        # Expression equivalence
        self.assertTrue(self.router.verify("x + x", {'expected': "2*x"}))
        self.assertTrue(self.router.verify("(x+1)^2", {'expected': "x^2 + 2*x + 1"}))

    def test_list_comparison(self):
        # Basic lists
        self.assertTrue(self.router.verify([1, 2, 3], {'expected': [1, 2, 3]}))
        
        # Multiset comparison (order shouldn't matter for numbers)
        self.assertTrue(self.router.verify([3, 1, 2], {'expected': [1, 2, 3]}))
        
        # Mixed types in list
        self.assertTrue(self.router.verify([1, "2.0"], {'expected': [1.0, 2]}))

    def test_reverse_check(self):
        # Reverse expression check: If answer is x, check if x^2 == 4
        context = {
            'reverse_expression': '{x}^2',
            'reverse_target': 4
        }
        self.assertTrue(self.router.verify(2, context))
        self.assertTrue(self.router.verify(-2, context))
        self.assertFalse(self.router.verify(3, context))

if __name__ == '__main__':
    unittest.main()
