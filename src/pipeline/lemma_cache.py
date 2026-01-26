"""Lemma / Pattern Cache (Prototype)

Stores normalized SymPy expressions encountered during successful solutions.
Tracks usage counts to enable future retrieval & prompt conditioning.
"""
from __future__ import annotations
from typing import Dict

try:
    import sympy as sp
except ImportError:
    sp = None

class LemmaCache:
    def __init__(self):
        self.store: Dict[str, int] = {}

    def add(self, expr_text: str) -> bool:
        if not expr_text:
            return False
        key = self._normalize(expr_text)
        if not key:
            return False
        hit = key in self.store
        self.store[key] = self.store.get(key, 0) + 1
        return hit

    def top(self, k: int = 10):
        return sorted(self.store.items(), key=lambda x: x[1], reverse=True)[:k]

    def _normalize(self, text: str) -> str:
        if not sp:
            return text.strip()
        try:
            expr = sp.sympify(text)
            expr = sp.simplify(expr)
            return str(expr)
        except Exception:
            return text.strip()

GLOBAL_LEMMA_CACHE = LemmaCache()

__all__ = ['LemmaCache', 'GLOBAL_LEMMA_CACHE']
