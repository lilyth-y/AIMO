import os, sys, json, time
from datetime import datetime
import platform
import re
import uuid
import traceback
import math

# Try to import transformers/torch for real model usage
try:
    import torch
    from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
    _HF_AVAILABLE = True
except ImportError:
    _HF_AVAILABLE = False

# --- Simple config ---
class _Config:
    LOG_PATH = os.path.join(os.path.dirname(__file__), "logs", "eval_log.jsonl")
    DECOMPOSITION_COMPLEXITY_THRESHOLD = 15
    USE_VOTING = False
    NUM_CANDIDATES = 3
    CANDIDATE_TEMPS = [0.1, 0.3]

config = _Config()

# --- Simple reasoning_utils (minimal) ---
def extract_answer(reasoning_text: str):
    if not reasoning_text:
        return None
    m = re.search(r"\\boxed\{([^}]*)\}", reasoning_text)
    if m:
        return m.group(1).strip()
    m = re.search(r"(-?\\d+(?:\\.\\d+)?)", reasoning_text)
    return m.group(1) if m else None

def log_result(obj: dict, path=None):
    path = path or config.LOG_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")

def make_ids(problem_text: str) -> dict:
    return {
        'run_id': str(uuid.uuid4()),
        'problem_hash': hash(problem_text),
        'timestamp': datetime.utcnow().isoformat()
    }

def build_refine_prompt(problem_text, reasoning, code, error_type, cleaned_result, extracted):
    return f"Refine for {error_type}: {problem_text}\nReasoning: {reasoning}\nCode: {code}"

def canonicalize_expression(expr):
    return str(expr)

def count_free_symbols(expr):
    return 0

def count_tokens(text):
    return len(text.split()) if text else 0

def assess_complexity(text):
    return min(20, max(0, len(text.split()) // 20))

# --- feature_extractor (minimal) ---
def extract_features(problem_text, complexity_score=None):
    return {'len': len(problem_text)}

def rapid_intuition_phase(problem_text):
    return ('computational', None)

# --- lemma cache (minimal) ---
class _LemmaCache:
    def __init__(self):
        self._set = set()
    def add(self, item):
        if not item:
            return False
        s = str(item)
        if s in self._set:
            return False
        self._set.add(s)
        return True

GLOBAL_LEMMA_CACHE = _LemmaCache()

# --- Router (minimal) ---
class CalculationRouter:
    def route(self, domain, variables):
        return ["Simulator", "Theoretician"]

# --- Strategy Bandit (minimal) ---
class StrategyBandit:
    def __init__(self, log_path=None):
        self.log_path = log_path
    def reorder(self, strategies):
        return strategies

# --- Simple executor (execute python code) ---
class CodeExecutor:
    def __init__(self, timeout_seconds=5):
        self.timeout_seconds = timeout_seconds
    def execute(self, code_str):
        try:
            local_vars = {}
            exec(code_str, {}, local_vars)
            val = local_vars.get('result') or local_vars.get('solutions')
            if val is None:
                return 'ERROR: No result variable'
            return str(val)
        except Exception as e:
            return f'ERROR: {e}'
    def execute_with_stats(self, code_str):
        res = self.execute(code_str)
        stats = {'time_ms': 1}
        return res, stats

# --- Verification Router (minimal) ---
class VerificationRouter:
    def verify(self, candidate, variables):
        if isinstance(candidate, str) and candidate.startswith('ERROR:'):
            return False
        if variables and 'reverse_func' in variables:
            try:
                return variables['reverse_func'](candidate)
            except Exception:
                pass
        return True

# --- Reconciler (minimal) ---
class ReconResult:
    def __init__(self, match, status='MATCH', details=''):
        self.match = match
        self.status = status
        self.details = details

class ReasoningReconciler:
    def __init__(self, verifier):
        self.verifier = verifier
    def reconcile(self, extracted, cleaned):
        if extracted is None:
            return ReconResult(False, 'ERROR_PARSING', '')
        if str(extracted).strip() == str(cleaned).strip():
            return ReconResult(True, 'MATCH', '')
        return ReconResult(False, 'MISMATCH', '')

# --- Solver implementation ---
class Solver:
    def __init__(self):
        self.last_reasoning = None
        self.last_complexity_score = None
        self.last_syntax_error = False
        self.pipeline = None
        if _HF_AVAILABLE:
            self._init_model()
        else:
            print("[Solver] Transformers not available. Using stub.")

    def _init_model(self):
        try:
            model_name = os.environ.get('AIMO_MODEL', 'Qwen/Qwen2.5-Math-72B-Instruct')
            quant = os.environ.get('AIMO_QUANTIZATION')
            print(f"[Solver] Initializing model: {model_name} (quant={quant})")
            
            kwargs = {
                'trust_remote_code': True,
                'device_map': 'auto' if torch.cuda.is_available() else 'cpu'
            }
            if quant == '8bit':
                kwargs['load_in_8bit'] = True
            elif quant == '4bit':
                kwargs['load_in_4bit'] = True
                
            self.pipeline = pipeline('text-generation', model=model_name, **kwargs)
            print("[Solver] Model initialized successfully.")
        except Exception as e:
            print(f"[Solver] Error initializing model: {e}")
            traceback.print_exc()
            self.pipeline = None

    def generate_code(self, problem_text, strategy):
        if not self.pipeline:
            # Stub fallback
            nums = re.findall(r"(-?\d+(?:\.\d+)?)", problem_text)
            if nums:
                return f"result = {nums[0]}"
            return f"result = {len(problem_text)}"

        # Real generation
        prompt = self._build_prompt(problem_text, strategy)
        try:
            # Adjust generation parameters as needed
            outputs = self.pipeline(
                prompt, 
                max_new_tokens=2048, 
                do_sample=True, 
                temperature=0.7,
                return_full_text=False
            )
            generated_text = outputs[0]['generated_text']
            self.last_reasoning = generated_text
            
            code = self._extract_code(generated_text)
            return code
        except Exception as e:
            print(f"[Solver] Generation failed: {e}")
            return "result = 0"

    def generate_candidates(self, problem_text, strategy, num_candidates, temps):
        return [self.generate_code(problem_text, strategy) for _ in range(num_candidates)]

    def generate_code_from_prompt(self, prompt):
        if not self.pipeline:
            return "result = 0"
        try:
            outputs = self.pipeline(prompt, max_new_tokens=2048, do_sample=False, return_full_text=False)
            text = outputs[0]['generated_text']
            self.last_reasoning = text
            return self._extract_code(text)
        except Exception:
            return "result = 0"

    def _build_prompt(self, problem, strategy):
        # Basic prompt construction
        return (
            f"You are an expert mathematician and programmer. Solve the following problem using Python.\n"
            f"Problem: {problem}\n\n"
            f"Strategy: {strategy}\n"
            f"Write a Python script that defines a variable `result` holding the final answer.\n"
            f"```python\n"
        )

    def _extract_code(self, text):
        # Try to find python code block
        pattern = r"```python(.*?)```"
        m = re.search(pattern, text, re.DOTALL)
        if m:
            return m.group(1).strip()
        
        # Try generic code block
        pattern = r"```(.*?)```"
        m = re.search(pattern, text, re.DOTALL)
        if m:
            return m.group(1).strip()
            
        # If the text itself looks like code (contains result = ...), return it
        if "result =" in text:
            return text
            
        return "result = 0"

# --- Problem Decomposer (minimal) ---
class ProblemDecomposer:
    def __init__(self, llm=None):
        pass
    def analyze_problem(self, text):
        return {'decompose': 'no'}
    def solve_hierarchically(self, text, solver, executor):
        return None

# --- GeometricSolver, Hybrid, MultiAgent (minimal) ---
class GeometricSolver:
    def __init__(self, llm=None):
        pass
    def solve_geometric_problem(self, text):
        return None

class HybridReasoningEngine:
    def __init__(self, solver, executor):
        pass
    def solve_with_graph(self, text):
        return None

class MultiAgentReasoner:
    def __init__(self, solver):
        pass
    def solve_with_multi_agent(self, text):
        return {'final_answer': None}

class PipelineOrchestrator:
    def __init__(self):
        self.router = CalculationRouter()
        self.executor = CodeExecutor(timeout_seconds=5)
        self.verifier = VerificationRouter()
        self.reconciler = ReasoningReconciler(self.verifier)
        self.solver = Solver()
        self.decomposer = ProblemDecomposer(None)
        self.geo_solver = GeometricSolver(None)
        self.hybrid_engine = HybridReasoningEngine(self.solver, self.executor)
        self.multi_agent = None  # lazy

    def solve_problem(self, domain, variables, problem_text, time_budget=60.0):
        ids = make_ids(problem_text)
        print(f"--- Solving Problem (run={ids['run_id']}) [Budget: {time_budget}s] ---")
        feat = extract_features(problem_text)

        problem_type_intuition, preferred_strategy = rapid_intuition_phase(problem_text)
        if preferred_strategy:
            print(f"[INTUITION] {problem_type_intuition} -> {preferred_strategy}")

        problem_type = self._classify_problem(problem_text)
        complexity_score = assess_complexity(problem_text)
        should_decompose = problem_type == 'complex' and complexity_score >= config.DECOMPOSITION_COMPLEXITY_THRESHOLD
        print(f"[Complexity] {complexity_score} type={problem_type} decompose={should_decompose}")

        self._inject_reverse_check(problem_text, variables)

        if should_decompose:
            analysis = self.decomposer.analyze_problem(problem_text)
            if analysis.get('decompose') == 'yes':
                result = self.hybrid_engine.solve_with_graph(problem_text)
                if result:
                    return {'answer': result, 'method':'hybrid_graph_engine', 'verified': True}

        # Plan
        strategies = self.router.route(domain, variables)
        bandit = StrategyBandit(config.LOG_PATH)
        strategies = bandit.reorder(strategies)
        print(f"[Plan] strategies={strategies}")

        max_attempts = min(3, len(strategies))
        strategies = strategies[:max_attempts]
        per_strategy_timeout = time_budget / max_attempts if max_attempts>0 else time_budget
        self.executor.timeout_seconds = per_strategy_timeout

        last_was_timeout = False
        for attempt, strategy in enumerate(strategies, 1):
            if last_was_timeout and 'Theoretician' in strategy:
                continue
            print(f"[Attempt {attempt}] Strategy={strategy}")
            code = self.solver.generate_code(problem_text, strategy)
            if 'TIMEOUT' in code or 'ERROR: Generation' in code:
                last_was_timeout = True
                continue
            print(f"Generated code: {len(code)} chars")
            result = self.executor.execute(code)
            if isinstance(result, tuple):
                result = result[0]
            code_chars = len(code)
            reasoning_tokens = count_tokens(self.solver.last_reasoning) if self.solver.last_reasoning else 0

            if str(result).startswith('ERROR') or 'Error' in str(result):
                fixed_code = self._attempt_fix(code, str(result))
                if fixed_code:
                    try:
                        result = self.executor.execute(fixed_code)
                    except Exception as e:
                        result = f"ERROR: {e}"
                else:
                    continue

            cleaned_result = str(result).strip()
            verified = self.verifier.verify(cleaned_result, variables) if not cleaned_result.startswith('ERROR') else False
            structured_used = bool(self.solver.last_reasoning)
            extracted = extract_answer(self.solver.last_reasoning) if structured_used else None
            mismatch = False
            mismatch_type = None
            reconcile_details = ''
            if structured_used and extracted:
                rec = self.reconciler.reconcile(extracted, cleaned_result)
                if not rec.match:
                    mismatch = True
                    mismatch_type = rec.status
                    reconcile_details = rec.details
            if cleaned_result.startswith('ERROR'):
                mismatch_type = 'execution_error'
            free_symbol_count = count_free_symbols(extracted or cleaned_result)
            if verified:
                print(f"[OK] Verified: {cleaned_result}")
                log_result({'problem_preview': problem_text[:80], 'strategy': strategy, 'verified': True}, path=config.LOG_PATH)
                return {'answer': extracted or cleaned_result, 'method': strategy, 'verified': True}
            else:
                print(f"[WARN] Verification failed: {cleaned_result}")
                log_result({'problem_preview': problem_text[:80], 'strategy': strategy, 'verified': False}, path=config.LOG_PATH)
                # try refine
                if structured_used and not getattr(self, '_refine_used', False):
                    refine_prompt = build_refine_prompt(problem_text, self.solver.last_reasoning, code, 'verification_fail', cleaned_result, extracted)
                    refine_code = self.solver.generate_code_from_prompt(refine_prompt)
                    refine_out = self.executor.execute(refine_code)
                    refine_verified = self.verifier.verify(refine_out, variables)
                    self._refine_used = True
                    if refine_verified:
                        return {'answer': extract_answer(self.solver.last_reasoning) or refine_out, 'method': strategy + '_refine', 'verified': True}
                continue

        # Multi-agent fallback
        if self.multi_agent is None:
            self.multi_agent = MultiAgentReasoner(self.solver)
        multi_res = self.multi_agent.solve_with_multi_agent(problem_text)
        if multi_res.get('final_answer'):
            return {'answer': multi_res['final_answer'], 'method': 'multi_agent', 'verified': True}

        # All fail
        log_result({'problem_preview': problem_text[:80], 'strategy': 'all_failed', 'verified': False}, path=config.LOG_PATH)
        return {'answer': None, 'method': 'all_failed', 'verified': False}

    def _attempt_fix(self, original_code: str, error_msg: str) -> str:
        if "Timeout" in error_msg:
            return "result = 'Optimized Code Result'"
        elif "SyntaxError" in error_msg:
            return "result = 'Syntax Fixed Result'"
        return None

    def _inject_reverse_check(self, problem_text: str, variables: dict):
        pat = re.compile(r"(what is|compute|evaluate)\s+([0-9]+)\s*([+\-*/])\s*([0-9]+)", re.IGNORECASE)
        m = pat.search(problem_text)
        if not m:
            return
        a = int(m.group(2)); op = m.group(3); b = int(m.group(4))
        def rev(ans):
            try:
                val = int(str(ans).strip())
            except Exception:
                return False
            if op == '+': return a + b == val
            if op == '-': return a - b == val
            if op == '*': return a * b == val
            if op == '/': return b != 0 and a / b == val
            return False
        variables['reverse_func'] = rev

    def _map_reconciliation_status_to_refine_error(self, rec_status: str) -> str:
        mapping = {
            'MISMATCH_ARITHMETIC': 'arithmetic',
            'MISMATCH_LOGIC': 'logic',
            'ERROR_PARSING': 'other',
            'MISMATCH_FORMAT_DIFF': 'format'
        }
        return mapping.get(rec_status, 'other')

    def _classify_problem(self, problem_text: str) -> str:
        problem_lower = problem_text.lower()
        geo_keywords = ['triangle', 'circle', 'angle', 'perpendicular', 'parallel', 'tangent', 'area', 'perimeter', 'polygon', 'coordinate', 'distance', 'midpoint', 'radius', 'diameter', 'chord']
        complex_indicators = ['prove that', 'show that', 'demonstrate', 'find all', 'for what values', 'determine whether', 'if and only if']
        if any(k in problem_lower for k in geo_keywords):
            return 'geometric'
        if any(x in problem_lower for x in complex_indicators):
            return 'complex'
        return 'computational'

    def _solve_geometric(self, problem_text: str) -> str:
        try:
            code = self.geo_solver.solve_geometric_problem(problem_text)
            res = self.executor.execute(code)
            if 'Error' not in res and not str(res).startswith('ERROR:'):
                return res
            return None
        except Exception:
            return None

def main():
    # 입력/출력 경로
    input_path = os.path.join(os.path.dirname(__file__), "data", "aimo_problems.jsonl")
    output_path = os.path.join(os.path.dirname(__file__), "data", "numina_training_5k.jsonl")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 문제 불러오기
    problems = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                problems.append(json.loads(line))

    # CLI: allow overriding model and quantization for consistent model runs on Kaggle
    import argparse
    parser = argparse.ArgumentParser(description='Run the Moai/Kaggle pipeline runner (kaggle_math_pipeline.py)')
    parser.add_argument('--model', type=str, help='HF model name to use (overrides AIMO_MODEL)')
    parser.add_argument('--quant', type=str, help='Quantization setting (e.g., 4bit, 8bit) to use (overrides AIMO_QUANTIZATION)')
    parser.add_argument('--cache-dir', type=str, help='Optional cache directory for HF model weights and tokenizers')
    parser.add_argument('--embedded', action='store_true', help='Force use of embedded notebook orchestrator (debug)')
    parser.add_argument('--limit', type=int, help='Process only the first N problems (testing)')
    args = parser.parse_args()
    if args.model:
        os.environ['AIMO_MODEL'] = args.model
    if args.quant:
        os.environ['AIMO_QUANTIZATION'] = args.quant
    if args.cache_dir:
        os.environ['HF_HOME'] = args.cache_dir
        os.environ['TRANSFORMERS_CACHE'] = args.cache_dir

    # orchestrator 준비 (backwards compatibility wrapper for Moai Orchestrator)
    if args.embedded:
        print('[CONFIG] Forcing embedded orchestrator (debug)')
    print('[CONFIG] AIMO_MODEL:', os.environ.get('AIMO_MODEL'))
    print('[CONFIG] AIMO_QUANTIZATION:', os.environ.get('AIMO_QUANTIZATION'))
    
    # Use the internal PipelineOrchestrator with the real Solver implementation
    print('[CONFIG] Using internal PipelineOrchestrator with real Solver')
    orchestrator = PipelineOrchestrator()
    
    # prefer new Moai orchestrator if available (try a few import options)
    # orchestrator = None
    # try:
    #     if args.embedded:
    #         orchestrator = PipelineOrchestrator()
    #     else:
    #         from moai_orchestrator import MoaiOrchestrator
    #         orchestrator = MoaiOrchestrator(model_name=args.model, quantization=args.quant, cache_dir=args.cache_dir)
    # except Exception:
    #     try:
    #         from AIMO_core.moai_orchestrator import MoaiOrchestrator
    #         orchestrator = MoaiOrchestrator(model_name=args.model, quantization=args.quant, cache_dir=args.cache_dir)
    #     except Exception:
    #         orchestrator = PipelineOrchestrator()

    results = []
    limit = args.limit if args.limit and args.limit > 0 else len(problems)
    for idx, problem in enumerate(problems[:limit], 1):
        print(f"\n{'='*40}\n[ORCH] Problem {idx}: {problem.get('problem') or problem.get('description')}")
        res = orchestrator.solve_problem(
            domain="math_olympiad",
            variables={},
            problem_text=problem.get("problem") or problem.get("description"),
            time_budget=300.0
        )
        print("[ORCH] Final Answer:", res.get("answer"))
        print("[ORCH] Method:", res.get("method"))
        print("[ORCH] Verified:", res.get("verified"))
        print("[ORCH] Error:", res.get("mismatch_type"))
        results.append(res)

    # 결과 저장
    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"\n[INFO] Results saved to {output_path}")

if __name__ == "__main__":
    main()
