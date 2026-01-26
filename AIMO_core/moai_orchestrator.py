import os, sys, json, re, uuid
from datetime import datetime
from collections import defaultdict
import random
import math  # Added to resolve math dependency

class _Config:
    LOG_PATH = os.path.join(os.path.dirname(__file__), "logs", "eval_log.jsonl")
    DECOMPOSITION_COMPLEXITY_THRESHOLD = 15
    USE_VOTING = False
    NUM_CANDIDATES = 3
    CANDIDATE_TEMPS = [0.1, 0.3]

config = _Config()

def make_ids(problem_text: str) -> dict:
    return {
        'run_id': str(uuid.uuid4()),
        'problem_hash': hash(problem_text),
        'timestamp': datetime.utcnow().isoformat()
    }

def log_result(obj: dict, path=None):
    path = path or config.LOG_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")

class StrategyBandit:
    """Implements a simple Upper Confidence Bound (UCB) strategy bandit."""
    def __init__(self):
        self.rewards = defaultdict(float)
        self.counts = defaultdict(int)

    def select_strategy(self, strategies):
        """Selects the best strategy based on UCB."""
        total_counts = sum(self.counts.values()) + 1e-5  # Avoid division by zero
        ucb_values = {
            strategy: (self.rewards[strategy] / (self.counts[strategy] + 1e-5)) +
                      max(0, (2 * (2 * max(1e-5, math.log(total_counts)) / (self.counts[strategy] + 1e-5)) ** 0.5))
            for strategy in strategies
        }
        # Ensure UCB values are real numbers
        ucb_values = {k: float(v) for k, v in ucb_values.items()}
        return max(ucb_values, key=ucb_values.get)

    def update(self, strategy, reward):
        """Updates the reward and count for a strategy."""
        self.rewards[strategy] += reward
        self.counts[strategy] += 1

class MultiAgentReasoner:
    """Coordinates multiple agents to solve a problem."""
    def __init__(self, agents):
        self.agents = agents

    def solve(self, domain, variables, problem_text):
        """Aggregates responses from multiple agents."""
        responses = [json.dumps(agent.solve(domain, variables, problem_text), sort_keys=True) for agent in self.agents]
        # Decode the selected response back to a dictionary
        return json.loads(max(set(responses), key=responses.count))

class HybridReasoningEngine:
    """Combines simulation and theoretical approaches."""
    def solve(self, domain, variables, problem_text):
        """Chooses the best approach dynamically."""
        if len(variables) < config.DECOMPOSITION_COMPLEXITY_THRESHOLD:
            return "Simulator"
        return "Theoretician"

class MoaiOrchestrator:
    """A small wrapper that prefers the full `PipelineOrchestrator` from the `src.pipeline` package
    when available, and falls back to a lightweight in-file orchestrator when not.
    This makes the Moai orchestrator self-contained for Kaggle/Colab while compatible with the
    main codebase when present.
    """
    def __init__(self, model_name=None, quantization=None, cache_dir=None):
        self.impl = None
        # Allow explicit config via constructor; these will set ENV vars so other modules (Solver) pick them up
        if model_name:
            os.environ['AIMO_MODEL'] = str(model_name)
        if quantization:
            os.environ['AIMO_QUANTIZATION'] = str(quantization)
        if cache_dir:
            os.environ['HF_HOME'] = str(cache_dir)
            os.environ['TRANSFORMERS_CACHE'] = str(cache_dir)

        print(f"[MoaiOrchestrator] Using model={os.environ.get('AIMO_MODEL')} quant={os.environ.get('AIMO_QUANTIZATION')} cache={os.environ.get('TRANSFORMERS_CACHE')}")
        try:
            import torch
            print(f"[MoaiOrchestrator] Torch available: {torch.__version__}; CUDA: {torch.cuda.is_available()}")
        except Exception:
            print("[MoaiOrchestrator] Torch not available or not imported")
        # warn about quantization availability
        if os.environ.get('AIMO_QUANTIZATION'):
            try:
                import bitsandbytes as bnb
            except Exception:
                print("[WARNING] `bitsandbytes` not installed; quantization may not be available.")
        # Try to use the full orchestrator if present (project root `src.pipeline.orchestrator`)
        try:
            from src.pipeline.orchestrator import PipelineOrchestrator as FullOrch
            self.impl = FullOrch()
            self._is_full = True
        except Exception:
            self.impl = None
            self._is_full = False
        if not self._is_full:
            # Build a minimal inlined orchestrator similar to the lightweight `kaggle_math_pipeline` fallback
            class LightweightOrch:
                def __init__(self):
                    # Implement a minimal in-process orchestrator to avoid circular imports
                    self.router = lambda domain, variables: ["Simulator", "Theoretician"]
                    self.timeout_seconds = 5
                def solve_problem(self, domain, variables, problem_text, time_budget=60.0):
                    # Very small heuristic: extract the first number in the problem text
                    import re
                    m = re.search(r"(-?\d+(?:\.\d+)?)", problem_text)
                    ans = m.group(1) if m else None
                    return {'answer': ans, 'method': 'lightweight_simulator', 'verified': False}
                def solve(self, domain, variables, problem_text):
                    return self.solve_problem(domain, variables, problem_text)
            try:
                self.impl = LightweightOrch()
            except Exception:
                # Last resort: very small fallback implementation
                class Fallback:
                    def solve_problem(self, domain, variables, problem_text, time_budget=60.0):
                        # naive: extract the first number as the answer
                        import re
                        m = re.search(r"(-?\d+(?:\.\d+)?)", problem_text)
                        ans = m.group(1) if m else None
                        return {'answer': ans, 'method': 'fallback', 'verified': False}
                self.impl = Fallback()
        self.strategy_bandit = StrategyBandit()
        self.multi_agent_reasoner = MultiAgentReasoner(agents=[self.impl])
        self.hybrid_engine = HybridReasoningEngine()

    def solve_problem(self, domain, variables, problem_text, time_budget=60.0):
        ids = make_ids(problem_text)
        print(f"--- [MoaiOrchestrator] run={ids['run_id']} using {'full' if self._is_full else 'lightweight'} implementation ---")
        # Use HybridReasoningEngine to decide the path
        strategy = self.hybrid_engine.solve(domain, variables, problem_text)
        print(f"[MoaiOrchestrator] Selected strategy: {strategy}")
        # Use StrategyBandit to refine strategy selection
        strategy = self.strategy_bandit.select_strategy(["Simulator", "Theoretician"])
        print(f"[MoaiOrchestrator] Bandit-refined strategy: {strategy}")
        # Solve using MultiAgentReasoner
        result = self.multi_agent_reasoner.solve(domain, variables, problem_text)
        # Update bandit with a dummy reward for now
        self.strategy_bandit.update(strategy, reward=1.0)  # Placeholder reward
        return result


if __name__ == '__main__':
    # Quick smoke test
    orchestrator = MoaiOrchestrator()
    res = orchestrator.solve_problem(domain='math_olympiad', variables={}, problem_text='What is 12 + 30?')
    print('Smoketest result:', res)
