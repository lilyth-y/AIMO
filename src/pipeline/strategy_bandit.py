"""Strategy Bandit / Reordering Module

Provides lightweight adaptive ordering of strategies using log-derived
performance metrics. Current policy: epsilon-greedy on empirical success rate.

Success definition: log entry with `verified==True` and `strategy` not in
['all_failed', *_refine]. Each attempt counts as a trial.

If insufficient data (< MIN_TOTAL_TRIALS), returns original ordering.
"""
from __future__ import annotations
from typing import List, Dict
import json, os, random

DEFAULT_ORDER = ['Path C: The Hybrid', 'Path A: The Simulator', 'Path B: The Theoretician']
MIN_TOTAL_TRIALS = 15

class StrategyBandit:
    def __init__(self, log_path: str, epsilon: float = 0.15):
        self.log_path = log_path
        self.epsilon = epsilon
        self.stats: Dict[str, Dict[str, int]] = {s: {'success':0,'trials':0} for s in DEFAULT_ORDER}
        self._loaded = False

    def load(self):
        if not os.path.exists(self.log_path):
            return
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line=line.strip()
                    if not line: continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue
                    strat = entry.get('strategy')
                    if not strat or strat.endswith('_refine') or strat=='all_failed':
                        continue
                    if strat not in self.stats:
                        # initialize unseen strategy
                        self.stats[strat] = {'success':0,'trials':0}
                    self.stats[strat]['trials'] += 1
                    if entry.get('verified'):
                        self.stats[strat]['success'] += 1
            self._loaded = True
        except Exception:
            pass

    def total_trials(self) -> int:
        return sum(v['trials'] for v in self.stats.values())

    def success_rate(self, strat: str) -> float:
        s = self.stats.get(strat, {'success':0,'trials':0})
        if s['trials']==0:
            return 0.0
        return s['success']/s['trials']

    def reorder(self, original: List[str]) -> List[str]:
        if not self._loaded:
            self.load()
        if self.total_trials() < MIN_TOTAL_TRIALS:
            return original  # insufficient data
        # UCB scoring + epsilon exploration
        total = self.total_trials()
        import math
        scores = {}
        for s in original:
            stat = self.stats.get(s, {'success':0,'trials':0})
            t = stat['trials']
            if t == 0:
                scores[s] = float('inf')
            else:
                rate = stat['success']/t
                scores[s] = rate + math.sqrt(2*math.log(total)/t)
        if random.random() < self.epsilon:
            rnd = original[:]
            random.shuffle(rnd)
            return rnd
        return sorted(original, key=lambda s: scores.get(s,0), reverse=True)

__all__ = ['StrategyBandit']
