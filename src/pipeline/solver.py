"""
Solver Engine
- Handles the interaction with the "Intelligence" (Local LLM via HuggingFace)
- Generates code based on the selected strategy
"""

import re
import os
import threading
from typing import Optional
try:
    import torch  # type: ignore  # heavy; keep optional
except Exception:
    torch = None
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM # type: ignore
    from transformers import BitsAndBytesConfig # type: ignore
except Exception as e:
    print(f"[IMPORT ERROR] transformers import failed: {e}")
    pipeline = None
    AutoTokenizer = None
    AutoModelForCausalLM = None
    BitsAndBytesConfig = None
import gc
from . import config
from .reasoning_utils import build_structured_prompt, assess_complexity
from .lemma_cache import GLOBAL_LEMMA_CACHE

# Global LLM instance (shared across all Solver instances)
_GLOBAL_LLM_MODEL = None
_GLOBAL_LLM_TOKENIZER = None
_GLOBAL_LLM_PIPE = None

FAST_TEST = os.getenv("AIMO_FAST_TEST") == "1"


class LocalLLMClient:
    """Local LLM Client using HuggingFace Transformers"""

    def __init__(self, model_name=None, quantization=None):
        global _GLOBAL_LLM_MODEL, _GLOBAL_LLM_TOKENIZER, _GLOBAL_LLM_PIPE
        # Allow environment override so container runs can choose model via AIMO_MODEL/AIMO_QUANT
        env_model = os.getenv("AIMO_MODEL")
        env_quant = os.getenv("AIMO_QUANTIZATION")
        if model_name is None:
            model_name = env_model if env_model else config.HF_MODEL_NAME
        if quantization is None:
            quantization = env_quant if env_quant else config.QUANTIZATION_DEFAULT

        # Use quantized model for memory efficiency
        self.quantization = quantization
        self.model_name = model_name

        # Initialize tokenizer
        self.tokenizer = self._get_tokenizer(model_name)

        # Initialize model (lazy loading)
        self.model = None
        self.pipeline = None

    def _get_tokenizer(self, model_name):
        """Get tokenizer with proper setup. Handles local path and cache issues on Windows."""
        from huggingface_hub.utils import HFValidationError  # type: ignore
        # Prefer local files if a filesystem path is provided
        try:
            if os.path.exists(model_name):
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    local_files_only=True
                )
            else:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True
                )
        except Exception as e:
            # Some HF versions may try to validate a local cache path as a repo id; try local_files_only fallback
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    local_files_only=True
                )
            except Exception as e2:
                print(f"[Tokenizer Load Error] Failed to load tokenizer for {model_name}: {e2}")
                raise

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        return tokenizer

    def _get_model(self):
        """Lazy load the model with quantization."""
        global _GLOBAL_LLM_MODEL
        if _GLOBAL_LLM_MODEL is None:
            quantization_config = self._get_quantization_config()
            print(f"[INFO] Loading model: {self.model_name} with {self.quantization} quantization...")

            _GLOBAL_LLM_MODEL = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                trust_remote_code=True,
                quantization_config=quantization_config,
                torch_dtype=torch.float16 if self.quantization in ["4bit", "8bit"] else torch.float32
            )
            print(f"[SUCCESS] Model loaded successfully")
        return _GLOBAL_LLM_MODEL

    def _get_quantization_config(self):
        """Get quantization config for memory efficiency."""
        if self.quantization == "4bit":
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=False,
            )
        elif self.quantization == "8bit":
            return BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_compute_dtype=torch.float16,
            )
        else:
            return None  # Full precision

    def _get_pipeline(self):
        """Get or create the text generation pipeline."""
        global _GLOBAL_LLM_PIPE
        if _GLOBAL_LLM_PIPE is None:
            model = self._get_model()
            print("[INFO] Setting up text generation pipeline...")

            _GLOBAL_LLM_PIPE = pipeline(
                "text-generation",
                model=model,
                tokenizer=self.tokenizer,
                device_map="auto",
                torch_dtype=torch.float16,
                do_sample=True,
                temperature=0.1,
                max_new_tokens=512,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
            print("[SUCCESS] Pipeline ready")
        return _GLOBAL_LLM_PIPE

    def generate(self, prompt: str) -> str:
        """
        Generate code using local HuggingFace model.
        Always returns a string. Handles list/dict outputs robustly.
        """
        try:
            pipe = self._get_pipeline()

            # For MathCoder and similar chat/instruction models, format the prompt properly
            if "MathCoder" in self.model_name:
                formatted_prompt = f"### Problem:\n{prompt}\n\n### Solution:\n"
            else:
                formatted_prompt = prompt

            messages = [{"role": "user", "content": formatted_prompt}]
            outputs = pipe(
                messages,
                max_new_tokens=512,
                do_sample=False,
                num_return_sequences=1,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

            # Defensive: flatten list/dict outputs, always return str
            generated_text = None
            if outputs and len(outputs) > 0:
                out0 = outputs[0]
                if hasattr(out0, 'messages'):
                    generated_text = out0.messages[-1]['content']
                elif isinstance(out0, dict) and 'generated_text' in out0:
                    generated_text = out0['generated_text']
                    # Handle case where generated_text might be a list
                    if isinstance(generated_text, list):
                        generated_text = '\n'.join(str(x) for x in generated_text)
                    elif isinstance(generated_text, str):
                        if generated_text.startswith(formatted_prompt):
                            generated_text = generated_text[len(formatted_prompt):].strip()
                    else:
                        generated_text = str(generated_text)
                elif isinstance(out0, str):
                    generated_text = out0
                elif isinstance(out0, list):
                    # Join list elements as string
                    generated_text = '\n'.join(str(x) for x in out0)
                elif isinstance(out0, dict):
                    generated_text = str(out0)
                else:
                    generated_text = str(out0)

            if not generated_text or not isinstance(generated_text, str):
                generated_text = "print('NO RESPONSE')"

            return generated_text if generated_text.strip() else "```python\nprint('NO RESPONSE')\n```"

        except Exception as e:
            print(f"   -> Warning: Local model error: {e}")
            return f"```python\n# ERROR: Local model failed\nprint('ERROR: {str(e)}')\n```"

class Solver:
    def __init__(self):
        self.llm = LocalLLMClient()
        self.last_reasoning: Optional[str] = None  # stores structured reasoning when used
        self.last_syntax_error: bool = False

    def generate_code(self, problem_text: str, strategy: str) -> str:
        """Constructs prompt(s) and gets code from the LLM.
        If structured reasoning enabled, first obtain reasoning trace then code.
        """
        complexity_score = assess_complexity(problem_text)
        use_structured = (
            config.USE_STRUCTURED and
            (complexity_score >= config.COMPLEXITY_STRUCTURED_MIN_SCORE)
        )
        # Fallback: if complexity below threshold but length very large, still allow.
        if not use_structured and len(problem_text) >= config.STRUCTURED_LENGTH_THRESHOLD:
            use_structured = True
        # Store score for potential logging/analysis
        self.last_complexity_score = complexity_score
        reasoning_text = None
        if use_structured:
            reasoning_prompt = build_structured_prompt(problem_text) + "\n\nReturn ONLY the reasoning tags; do not produce code yet."
            reasoning_text = self.llm.generate(reasoning_prompt)
            self.last_reasoning = reasoning_text
        else:
            self.last_reasoning = None

        # Lemma cache injection (top 5) for guidance
        lemma_snippets = []
        top = GLOBAL_LEMMA_CACHE.top(5)
        if top:
            lemma_snippets = [k for k,_ in top]
        # Code prompt (includes reasoning context if available)
        prompt = self._construct_prompt(problem_text, strategy, reasoning_text if use_structured else None, lemma_snippets)
        response = self.llm.generate(prompt)
        code = self._extract_code(response)
        return code

    def generate_candidates(self, problem_text: str, strategy: str, num_candidates: int, temps):
        """Generate multiple candidate codes (sharing single reasoning) for voting."""
        complexity_score = assess_complexity(problem_text)
        use_structured = (
            config.USE_STRUCTURED and (complexity_score >= config.COMPLEXITY_STRUCTURED_MIN_SCORE)
        ) or (len(problem_text) >= config.STRUCTURED_LENGTH_THRESHOLD)
        self.last_complexity_score = complexity_score
        reasoning_text = None
        if use_structured:
            reasoning_prompt = build_structured_prompt(problem_text) + "\n\nReturn ONLY the reasoning tags; do not produce code yet."
            reasoning_text = self.llm.generate(reasoning_prompt)
            self.last_reasoning = reasoning_text
        else:
            self.last_reasoning = None
        lemma_snippets = []
        top = GLOBAL_LEMMA_CACHE.top(5)
        if top:
            lemma_snippets = [k for k,_ in top]
        candidates = []
        for i in range(num_candidates):
            temp = temps[i] if i < len(temps) else temps[-1]
            prompt = self._construct_prompt(problem_text, strategy, reasoning_text if use_structured else None, lemma_snippets)
            try:
                generated_text = self.llm.generate(prompt)
            except Exception:
                generated_text = "```python\nprint('ERROR: candidate generation failed')\n```"
            code = self._extract_code(generated_text)
            candidates.append(code)
        return candidates

    def _construct_prompt(self, problem_text: str, strategy: str, reasoning_text: Optional[str], lemma_snippets: list[str] | None = None) -> str:
        """Build the code generation prompt.
        reasoning_text: structured reasoning (tags) if previously generated.
        """
        max_problem_length = 500
        if len(problem_text) > max_problem_length:
            problem_text = problem_text[:max_problem_length] + "..."

        if "Simulator" in strategy:
            # Check if this is a puzzle problem (constraint satisfaction, logic puzzle)
            is_puzzle = any(kw in problem_text.lower() for kw in ['puzzle', '퍼즐', 'constraint', '제약', 'logic', '논리', 'satisfy', '만족'])
            
            if is_puzzle:
                base_instruction = (
                    "Write Python code to solve this puzzle/logic problem.\n"
                    "- Identify all constraints and conditions clearly\n"
                    "- Use constraint satisfaction, backtracking, or systematic search\n"
                    "- For small search spaces, try all possibilities\n"
                    "- For larger spaces, use logical deduction to narrow down candidates\n"
                    "- Store the final answer in a variable (e.g., 'answer' or 'result')\n"
                    "- Print ONLY the final answer as a single number or expression (no text, no labels)\n"
                    "- The printed output should be the exact answer: integer, fraction (a/b), or simplified expression\n"
                    "- No comments, no debug prints, no intermediate values"
                )
            else:
                base_instruction = (
                    "Write Python code to solve this problem by simulation.\n"
                    "- Use standard library or sympy\n"
                    "- Store the final answer in a variable (e.g., 'answer' or 'result')\n"
                    "- Print ONLY the final answer as a single number or expression (no text, no labels)\n"
                    "- The printed output should be the exact answer: integer, fraction (a/b), or simplified expression\n"
                    "- No comments, no debug prints, no intermediate values"
                )
        elif "Theoretician" in strategy:
            base_instruction = (
                "Write Python code using SymPy.\n"
                "- Import from sympy\n"
                "- Store the final answer in a variable (e.g., 'answer' or 'result')\n"
                "- Print ONLY the final answer as a single number or expression (no text, no labels)\n"
                "- Use sympy.simplify() to ensure canonical form\n"
                "- The printed output should be the exact answer: integer, fraction (a/b), or simplified expression\n"
                "- No comments, no debug prints, no intermediate values"
            )
        else:
            base_instruction = (
                "Write Python code to solve this.\n"
                "- Use standard library/numpy/sympy\n"
                "- Store the final answer in a variable (e.g., 'answer' or 'result')\n"
                "- Print ONLY the final answer as a single number or expression (no text, no labels)\n"
                "- The printed output should be the exact answer: integer, fraction (a/b), or simplified expression\n"
                "- No comments, no debug prints, no intermediate values"
            )

        lemma_block = ""
        if lemma_snippets:
            lemma_block = "Known canonical fragments (reuse if helpful):\n" + "\n".join(f"- {l}" for l in lemma_snippets) + "\n\n"
        if reasoning_text:
            prompt = (
                f"Structured reasoning (reference only):\n{reasoning_text}\n\n"
                f"{lemma_block}{base_instruction}\nProblem: {problem_text}\n\nCode:"
            )
        else:
            prompt = f"{lemma_block}{base_instruction}\nProblem: {problem_text}\n\nCode:"
        return prompt

    def generate_code_from_prompt(self, prompt: str) -> str:
        """
        Generates code from an already structured prompt.
        Used by HybridReasoningEngine.
        """
        response = self.llm.generate(prompt)
        return self._extract_code(response)
    
    def _extract_code(self, response: str) -> str:
        """
        Extracts code from markdown blocks if present and validates syntax.
        """
        code = response.strip()
        
        # Fix: Handle escaped strings (\\n -> \n)
        if '\\n' in code and code.count('\\n') > code.count('\n'):
            # Likely escaped string, try to decode
            try:
                # Try to unescape common escape sequences
                code = code.encode().decode('unicode_escape')
            except:
                # If that fails, manually replace common escapes
                code = code.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'")
        
        # Try to extract from markdown blocks
        match = re.search(r"```python\s*(.*?)\s*```", code, re.DOTALL)
        if match:
            code = match.group(1).strip()
        else:
            match = re.search(r"```\s*(.*?)\s*```", code, re.DOTALL)
            if match:
                code = match.group(1).strip()
        
        # Remove any leading/trailing non-code text
        lines = code.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            stripped = line.strip()
            # Start collecting when we see Python code keywords
            if any(stripped.startswith(kw) for kw in ['import ', 'from ', 'def ', 'class ', 'if ', 'for ', 'while ', '#']) or '=' in stripped or in_code:
                in_code = True
                code_lines.append(line)
            elif in_code and stripped:  # Continue if already in code
                code_lines.append(line)
        
        if code_lines:
            code = '\n'.join(code_lines)
        
        # Basic syntax validation
        try:
            compile(code, '<string>', 'exec')
            self.last_syntax_error = False
        except SyntaxError as e:
            print(f"   -> [WARNING] Syntax error detected: {e}")
            print(f"   -> [DEBUG] Problematic code: {repr(code[:200])}")
            self.last_syntax_error = True
            code = "print('ERROR: Code generation failed')"
        return code

# & C:/startingup/AIMO/.venv/Scripts/pip.exe install --upgrade transformers sentencepiece

