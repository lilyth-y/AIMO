"""
Solver Engine
- Handles the interaction with the "Intelligence" (Local LLM via HuggingFace)
- Generates code based on the selected strategy
"""

import re
import os

import warnings
from typing import Optional

try:
    import torch  # type: ignore  # heavy; keep optional
except Exception:
    torch = None
try:
    from transformers import (  # type: ignore
        pipeline,
        AutoTokenizer,
        AutoModelForCausalLM,
        BitsAndBytesConfig,
        GenerationConfig,
    )
except Exception as e:
    # Logger not available yet during import, use print for critical import errors
    print(f"[IMPORT ERROR] transformers import failed: {e}")
    pipeline = None
    AutoTokenizer = None
    AutoModelForCausalLM = None
    BitsAndBytesConfig = None
    GenerationConfig = None  # type: ignore[misc, assignment]
from . import config
from .reasoning_utils import build_structured_prompt, assess_complexity
from .lemma_cache import GLOBAL_LEMMA_CACHE
from .logger import get_logger

logger = get_logger()

# Global LLM instance (shared across all Solver instances)
_GLOBAL_LLM_MODEL = None
_GLOBAL_LLM_TOKENIZER = None
_GLOBAL_LLM_PIPE = None

FAST_TEST = os.getenv("AIMO_FAST_TEST") == "1"


class LocalLLMClient:
    """Local LLM Client using HuggingFace Transformers"""

    def __init__(self, model_name=None, quantization=None):
        global _GLOBAL_LLM_MODEL, _GLOBAL_LLM_TOKENIZER, _GLOBAL_LLM_PIPE
        # Allow environment override so container runs can choose model via OMI_MODEL/AIMO_QUANT
        env_model = os.getenv("OMI_MODEL")
        env_quant = os.getenv("MATHCODEORCHESTRATOR_QUANTIZATION")
        if model_name is None:
            model_name = env_model if env_model else config.HF_MODEL_NAME
        if quantization is None:
            quantization = env_quant if env_quant else config.QUANTIZATION_DEFAULT

        # Use quantized model for memory efficiency
        self.quantization = quantization
        self.model_name = model_name

        # Initialize tokenizer
        self.tokenizer = self._get_tokenizer(model_name)
        if getattr(self.tokenizer, "pad_token_id", None) is None:
            self.tokenizer.pad_token_id = getattr(self.tokenizer, "eos_token_id", 0)

        # Initialize model (lazy loading)
        self.model = None
        self.pipeline = None

    @staticmethod
    def _is_local_model_path(model_name: str) -> bool:
        """True only for real filesystem paths; HuggingFace repo_id (e.g. Org/Model) is False."""
        if model_name.startswith("/"):
            return True
        if len(model_name) > 2 and model_name[1:2] == ":":
            return True
        if os.path.sep in model_name and os.path.exists(model_name):
            return True
        return False

    def _get_tokenizer(self, model_name):
        """Get tokenizer with proper setup. Handles local path and cache issues on Windows."""

        is_local_path = self._is_local_model_path(model_name)

        # For local paths, use local_files_only=True (required for Windows cache paths)
        if is_local_path:
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name, trust_remote_code=True, local_files_only=True
                )
                logger.info(f"Loaded tokenizer from local path: {model_name}")
                return tokenizer
            except Exception as e:
                logger.error(
                    f"Failed to load tokenizer from local path {model_name}: {e}"
                )
                raise
        else:
            # For HuggingFace repo names, use standard loading
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name, trust_remote_code=True
                )
                logger.info(f"Loaded tokenizer from HuggingFace repo: {model_name}")
                return tokenizer
            except Exception as e:
                error_msg = (
                    f"Failed to load tokenizer from HuggingFace repo {model_name}: {e}"
                )
                logger.error(error_msg)
                raise

    def _get_model(self):
        """Lazy load the model with quantization."""
        global _GLOBAL_LLM_MODEL
        if _GLOBAL_LLM_MODEL is None:
            quantization_config = self._get_quantization_config()
            logger.info(
                f"Loading model: {self.model_name} with {self.quantization} quantization..."
            )

            is_local = self._is_local_model_path(self.model_name)
            kw = dict(
                device_map="auto",
                trust_remote_code=True,
                quantization_config=quantization_config,
                dtype=torch.float16,  # Always use fp16 to fit in 8GB VRAM (was torch_dtype, deprecated)
            )
            if is_local:
                kw["local_files_only"] = True

            try:
                _GLOBAL_LLM_MODEL = AutoModelForCausalLM.from_pretrained(
                    self.model_name, **kw
                )
                logger.info("Model loaded successfully")
            except Exception as e1:
                err_msg = str(e1)
                # GPU 부족으로 CPU 오프로드를 요구하는 오류면, max_memory로 재시도
                if (
                    (
                        "llm_int8_enable_fp32_cpu_offload" in err_msg
                        or "CPU or the disk" in err_msg
                        or "device_map" in err_msg
                    )
                    and self.quantization == "8bit"
                    and "max_memory" not in kw
                ):
                    try:
                        gpu_gb = 4
                        if (
                            torch is not None
                            and getattr(torch.cuda, "is_available", lambda: False)()
                        ):
                            gpu_mem = torch.cuda.get_device_properties(0).total_memory
                            gpu_gb = max(2, int(gpu_mem / (1024**3)) - 1)
                        kw["max_memory"] = {0: f"{gpu_gb}GiB", "cpu": "20GiB"}
                        _GLOBAL_LLM_MODEL = AutoModelForCausalLM.from_pretrained(
                            self.model_name, **kw
                        )
                        logger.info(
                            "Model loaded successfully (with CPU offload / max_memory)"
                        )
                    except Exception as e2:
                        logger.warning(f"Retry with max_memory failed: {e2}")
                        raise e1
                else:
                    raise
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
            # GPU 메모리 부족 시 CPU로 일부 오프로드 허용 (32-bit 유지)
            enable_cpu_offload = os.getenv("AIMO_LLM_INT8_CPU_OFFLOAD", "1") == "1"
            return BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_compute_dtype=torch.float16,
                llm_int8_enable_fp32_cpu_offload=enable_cpu_offload,
            )
        else:
            return None  # Full precision

    def _get_pipeline(self):
        """Get or create the text generation pipeline."""
        global _GLOBAL_LLM_PIPE
        if _GLOBAL_LLM_PIPE is None:
            model = self._get_model()
            logger.info("Setting up text generation pipeline...")

            # 생성 옵션은 generate() 호출 시에만 전달 (pipeline 생성 시 넣으면 호출 시와 중복되어 경고 발생)
            _GLOBAL_LLM_PIPE = pipeline(
                "text-generation",
                model=model,
                tokenizer=self.tokenizer,
                device_map="auto",
                dtype=torch.float16,
            )
            logger.info("Pipeline ready")
        return _GLOBAL_LLM_PIPE

    def generate(self, prompt: str, do_sample: bool = False, temperature: float = 0.1) -> str:
        """
        Generate code using local HuggingFace model or remote inference API.
        If OMI_REMOTE_INFERENCE_URL is set, calls that URL (computing engine = remote).
        """
        try:
            from .remote_inference import (
                is_remote_inference_configured,
                generate_remote,
            )

            if is_remote_inference_configured():
                if "MathCoder" in (self.model_name or ""):
                    formatted = f"### Problem:\n{prompt}\n\n### Solution:\n"
                else:
                    formatted = prompt
                return generate_remote(formatted)
        except Exception as e:
            logger.warning("Remote inference check failed, using local: %s", e)

        try:
            pipe = self._get_pipeline()

            # For MathCoder and similar chat/instruction models, format the prompt properly
            if "MathCoder" in self.model_name:
                formatted_prompt = f"### Problem:\n{prompt}\n\n### Solution:\n"
            else:
                formatted_prompt = prompt

            # tokenizer.chat_template이 없으면 messages 대신 문자열로 호출 (MathCoder 등)
            # Instruct 모델인데 템플릿이 없으면 기본적인 Qwen 템플릿 부여 시도
            if "Instruct" in (self.model_name or "") and getattr(self.tokenizer, "chat_template", None) is None:
                try:
                    self.tokenizer.chat_template = (
                        "{% for message in messages %}"
                        "{{ '<|im_start|>' + message['role'] + '\\n' + message['content'] + '<|im_end|>\\n' }}"
                        "{% endfor %}"
                        "{% if add_generation_prompt %}"
                        "{{ '<|im_start|>assistant\\n' }}"
                        "{% endif %}"
                    )
                except Exception:
                    pass

            use_messages = getattr(self.tokenizer, "chat_template", None) is not None
            max_tokens = int(os.getenv("AIMO_MAX_NEW_TOKENS", "10000000000000000000000000000000"))
            # GenerationConfig만 사용해 전달 (개별 인자와 중복 시 경고, max_length 미설정 시 pipeline 기본값 20과 충돌)
            gen_cfg_kw = dict(
                max_new_tokens=max_tokens,
                do_sample=do_sample,
                num_return_sequences=1,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                max_length=None,  # pipeline 기본 20과 충돌 방지
            )
            if do_sample:
                gen_cfg_kw["temperature"] = max(0.01, temperature)
            gen_config = GenerationConfig(**gen_cfg_kw)

            try:
                if use_messages:
                    outputs = pipe(
                        [{"role": "user", "content": formatted_prompt}],
                        generation_config=gen_config,
                    )
                else:
                    outputs = pipe(formatted_prompt, generation_config=gen_config)
            except Exception as e:
                if "chat_template" in str(e) or "chat template" in str(e).lower():
                    use_messages = False
                    outputs = pipe(formatted_prompt, generation_config=gen_config)
                else:
                    raise

            # Defensive: flatten list/dict outputs, always return str
            generated_text = None
            if outputs and len(outputs) > 0:
                out0 = outputs[0]
                if hasattr(out0, "messages"):
                    generated_text = out0.messages[-1]["content"]
                elif isinstance(out0, dict) and "generated_text" in out0:
                    generated_text = out0["generated_text"]
                    # Handle case where generated_text might be a list
                    if isinstance(generated_text, list):
                        generated_text = "\n".join(str(x) for x in generated_text)
                    elif isinstance(generated_text, str):
                        if generated_text.startswith(formatted_prompt):
                            generated_text = generated_text[
                                len(formatted_prompt) :
                            ].strip()
                    else:
                        generated_text = str(generated_text)
                elif isinstance(out0, str):
                    generated_text = out0
                elif isinstance(out0, list):
                    # Join list elements as string
                    generated_text = "\n".join(str(x) for x in out0)
                elif isinstance(out0, dict):
                    generated_text = str(out0)
                else:
                    generated_text = str(out0)

            if not generated_text or not isinstance(generated_text, str):
                generated_text = "print('NO RESPONSE')"

            return (
                generated_text
                if generated_text.strip()
                else "```python\nprint('NO RESPONSE')\n```"
            )

        except Exception as e:
            logger.warning(f"Local model error: {e}")
            # 전체 예외 메시지(예: 32-bit 등)가 실행 결과로 나가 숫자가 추출되는 것을 막기 위해 짧은 메시지만 사용
            return "```python\n# ERROR: Local model failed\nprint('ERROR: Model load failed')\n```"


class Solver:
    def __init__(self):
        self.llm = LocalLLMClient()
        self.last_reasoning: Optional[str] = (
            None  # stores structured reasoning when used
        )
        self.last_syntax_error: bool = False

    def generate_code(self, problem_text: str, strategy: str) -> str:
        """Constructs prompt(s) and gets code from the LLM.
        If structured reasoning enabled, first obtain reasoning trace then code.
        """
        complexity_score = assess_complexity(problem_text)
        use_structured = config.USE_STRUCTURED and (
            complexity_score >= config.COMPLEXITY_STRUCTURED_MIN_SCORE
        )
        # Fallback: if complexity below threshold but length very large, still allow.
        if (
            not use_structured
            and len(problem_text) >= config.STRUCTURED_LENGTH_THRESHOLD
        ):
            use_structured = True
        # Store score for potential logging/analysis
        self.last_complexity_score = complexity_score
        reasoning_text = None
        if use_structured:
            reasoning_prompt = (
                build_structured_prompt(problem_text)
                + "\n\nReturn ONLY the reasoning tags; do not produce code yet."
            )
            reasoning_text = self.llm.generate(reasoning_prompt)
            self.last_reasoning = reasoning_text
        else:
            self.last_reasoning = None

        # Lemma cache injection (top 5) for guidance
        lemma_snippets = []
        top = GLOBAL_LEMMA_CACHE.top(5)
        if top:
            lemma_snippets = [k for k, _ in top]
        # Code prompt (includes reasoning context if available)
        prompt = self._construct_prompt(
            problem_text,
            strategy,
            reasoning_text if use_structured else None,
            lemma_snippets,
        )
        response = self.llm.generate(prompt)
        code = self._extract_code(response)
        return code

    def generate_candidates(
        self, problem_text: str, strategy: str, num_candidates: int, temps: list[float]
    ) -> list[str]:
        """Generate multiple candidate codes (sharing single reasoning) for voting."""
        complexity_score = assess_complexity(problem_text)
        use_structured = (
            config.USE_STRUCTURED
            and (complexity_score >= config.COMPLEXITY_STRUCTURED_MIN_SCORE)
        ) or (len(problem_text) >= config.STRUCTURED_LENGTH_THRESHOLD)
        self.last_complexity_score = complexity_score
        reasoning_text = None
        if use_structured:
            reasoning_prompt = (
                build_structured_prompt(problem_text)
                + "\n\nReturn ONLY the reasoning tags; do not produce code yet."
            )
            reasoning_text = self.llm.generate(reasoning_prompt)
            self.last_reasoning = reasoning_text
        else:
            self.last_reasoning = None
        lemma_snippets = []
        top = GLOBAL_LEMMA_CACHE.top(5)
        if top:
            lemma_snippets = [k for k, _ in top]
        candidates = []
        for i in range(num_candidates):
            # Pass temperature and allow sampling
            temp = temps[i] if temps and i < len(temps) else 0.7
            prompt = self._construct_prompt(
                problem_text,
                strategy,
                reasoning_text if use_structured else None,
                lemma_snippets,
            )
            try:
                generated_text = self.llm.generate(prompt, do_sample=True, temperature=temp)
            except Exception:
                generated_text = (
                    "```python\nprint('ERROR: candidate generation failed')\n```"
                )
            code = self._extract_code(generated_text)
            candidates.append(code)
        return candidates

    def _construct_prompt(
        self,
        problem_text: str,
        strategy: str,
        reasoning_text: Optional[str],
        lemma_snippets: list[str] | None = None,
    ) -> str:
        """Build the code generation prompt.
        reasoning_text: structured reasoning (tags) if previously generated.
        """
        max_problem_length = 500
        if len(problem_text) > max_problem_length:
            problem_text = problem_text[:max_problem_length] + "..."

        if "Simulator" in strategy:
            # Check if this is a puzzle problem (constraint satisfaction, logic puzzle)
            is_puzzle = any(
                kw in problem_text.lower()
                for kw in [
                    "puzzle",
                    "퍼즐",
                    "constraint",
                    "제약",
                    "logic",
                    "논리",
                    "satisfy",
                    "만족",
                ]
            )

            if is_puzzle:
                base_instruction = (
                    "Write Python code to solve this puzzle/logic problem.\n"
                    "- Identify all constraints and conditions clearly\n"
                    "- Use constraint satisfaction, backtracking, or systematic search\n"
                    "- For small search spaces, try all possibilities\n"
                    "- For larger spaces, use logical deduction to narrow down candidates; avoid storing 2^N states (memory limit ~2GB)\n"
                    "- Prefer iteration/generators over huge lists; cap brute-force N if needed\n"
                    "- Store the final answer in a variable (e.g., 'answer' or 'result')\n"
                    "- Print ONLY the final answer as a single number or expression (no text, no labels)\n"
                    "- The printed output should be the exact answer: integer, fraction (a/b), or simplified expression\n"
                    "- No comments, no debug prints, no intermediate values"
                )
            else:
                base_instruction = (
                    "Write Python code to solve this problem by simulation.\n"
                    "- Use standard library or sympy\n"
                    "- Keep memory under ~2GB: avoid huge lists/matrices; use iteration or sampling for large N\n"
                    "- Store the final answer in a variable (e.g., 'answer' or 'result')\n"
                    "- Print ONLY the final answer as a single number or expression (no text, no labels)\n"
                    "- The printed output should be the exact answer: integer, fraction (a/b), or simplified expression\n"
                    "- No comments, no debug prints, no intermediate values"
                )
        elif "Theoretician" in strategy:
            base_instruction = (
                "Write Python code using SymPy.\n"
                "- Start with: from sympy import symbols, solve, simplify, Eq, sympify, S; or use sympy.xxx (sympy is available in the environment)\n"
                "- Store the final answer in a variable (e.g., 'answer' or 'result')\n"
                "- Print ONLY the final answer as a single number or expression (no text, no labels)\n"
                "- Use sympy.simplify() to ensure canonical form\n"
                "- The printed output should be the exact answer: integer, fraction (a/b), or simplified expression\n"
                "- No comments, no debug prints, no intermediate values"
            )
        else:
            base_instruction = (
                "Write Python code to solve this.\n"
                "- Use standard library; math and sympy are available (use 'import sympy' or 'from sympy import ...' if using SymPy)\n"
                "- Store the final answer in a variable (e.g., 'answer' or 'result')\n"
                "- Print ONLY the final answer as a single number or expression (no text, no labels)\n"
                "- The printed output should be the exact answer: integer, fraction (a/b), or simplified expression\n"
                "- No comments, no debug prints, no intermediate values"
            )

        lemma_block = ""
        if lemma_snippets:
            lemma_block = (
                "Known canonical fragments (reuse if helpful):\n"
                + "\n".join(f"- {lemma}" for lemma in lemma_snippets)
                + "\n\n"
            )
        if reasoning_text:
            prompt = (
                f"Structured reasoning (reference only):\n{reasoning_text}\n\n"
                f"{lemma_block}{base_instruction}\nProblem: {problem_text}\n\nCode:"
            )
        else:
            prompt = (
                f"{lemma_block}{base_instruction}\nProblem: {problem_text}\n\nCode:"
            )
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
        if "\\n" in code and code.count("\\n") > code.count("\n"):
            # Likely escaped string, try to decode
            try:
                # Try to unescape common escape sequences
                code = code.encode().decode("unicode_escape")
            except (UnicodeDecodeError, ValueError):
                # If that fails, manually replace common escapes
                code = (
                    code.replace("\\n", "\n")
                    .replace("\\t", "\t")
                    .replace('\\"', '"')
                    .replace("\\'", "'")
                )

        # Try to extract from markdown blocks
        match = re.search(r"```python\s*(.*?)\s*```", code, re.DOTALL)
        if match:
            code = match.group(1).strip()
        else:
            match = re.search(r"```\s*(.*?)\s*```", code, re.DOTALL)
            if match:
                code = match.group(1).strip()

        # Remove any leading/trailing non-code text
        lines = code.split("\n")
        code_lines = []
        in_code = False

        for line in lines:
            stripped = line.strip()
            # Start collecting when we see Python code keywords
            if (
                any(
                    stripped.startswith(kw)
                    for kw in [
                        "import ",
                        "from ",
                        "def ",
                        "class ",
                        "if ",
                        "for ",
                        "while ",
                        "#",
                    ]
                )
                or "=" in stripped
                or in_code
            ):
                in_code = True
                code_lines.append(line)
            elif in_code and stripped:  # Continue if already in code
                code_lines.append(line)

        if code_lines:
            code = "\n".join(code_lines)

        # Basic syntax validation (with optional fix for invalid decimal literal)
        try:
            compile(code, "<string>", "exec")
            self.last_syntax_error = False
        except SyntaxError as e:
            if "invalid decimal literal" in str(e):
                # e.g. 09.5, 012, 01 -> fix leading zeros and retry once
                fixed = re.sub(r"\b0+([1-9]\d*(?:\.\d*)?)\b", r"\1", code)
                try:
                    compile(fixed, "<string>", "exec")
                    code = fixed
                    self.last_syntax_error = False
                    logger.debug("Fixed invalid decimal literal (leading zeros) and recompiled.")
                    return code
                except SyntaxError:
                    pass
            logger.warning(f"Syntax error detected: {e}")
            if len(code) > 200:
                logger.debug(f"Problematic code: {repr(code[:200])}...")
            else:
                logger.debug(f"Problematic code: {repr(code)}")
            self.last_syntax_error = True
            code = "print('ERROR: Code generation failed')"
        return code


# Note: Install transformers and sentencepiece if needed:
# pip install --upgrade transformers sentencepiece
