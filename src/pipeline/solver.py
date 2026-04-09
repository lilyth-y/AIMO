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

_VERTEX_SKIP_LOGGED = False


def _log_vertex_skipped_once() -> None:
    """Log once when Vertex is not configured so local HF is used (helps Cloud Shell debugging)."""
    global _VERTEX_SKIP_LOGGED
    if _VERTEX_SKIP_LOGGED:
        return
    _VERTEX_SKIP_LOGGED = True
    has_proj = bool((os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or "").strip())
    has_key = bool((os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("VERTEX_AI_API_KEY") or "").strip())
    logger.info(
        "Vertex Gemini not configured in this process (project=%s, api_key=%s); "
        "using remote or local HF. Export GOOGLE_CLOUD_PROJECT or API key before python.",
        "set" if has_proj else "unset",
        "set" if has_key else "unset",
    )


# Global LLM instance (shared across all Solver instances)
_GLOBAL_LLM_MODEL = None
_GLOBAL_LLM_TOKENIZER = None
_GLOBAL_LLM_PIPE = None

def _aimo_fast_test_enabled() -> bool:
    """
    True when ``AIMO_FAST_TEST=1``: use MockSolver, skip local HF model.
    Emit code from ``AIMO_MOCK_GENERATED_CODE`` (see ``mock_solver``); does not solve tasks.
    """
    return os.getenv("AIMO_FAST_TEST", "0") == "1"


def reset_global_llm_cache() -> None:
    """
    로드된 HF 모델·토크나이저·text-generation 파이프라인 전역 캐시를 비운다.
    테스트 격리 또는 모델/환경 전환 시 사용.
    """
    global _GLOBAL_LLM_MODEL, _GLOBAL_LLM_TOKENIZER, _GLOBAL_LLM_PIPE
    _GLOBAL_LLM_MODEL = None
    _GLOBAL_LLM_TOKENIZER = None
    _GLOBAL_LLM_PIPE = None


def _dtype_for_local_weights(quantization_config) -> "torch.dtype":
    """양자화 없을 때 ``AIMO_LLM_DTYPE`` (float16|float32|bfloat16). 양자화 시 fp16 고정."""
    if torch is None:
        raise RuntimeError("torch required for local LLM")
    if quantization_config is not None:
        return torch.float16
    d = os.getenv("AIMO_LLM_DTYPE", "float16").strip().lower()
    if d in ("float32", "fp32"):
        return torch.float32
    if d in ("bfloat16", "bf16"):
        return torch.bfloat16
    return torch.float16


class LocalLLMClient:
    """Local LLM Client using HuggingFace Transformers"""

    def __init__(self, model_name=None, quantization=None):
        global _GLOBAL_LLM_MODEL, _GLOBAL_LLM_TOKENIZER, _GLOBAL_LLM_PIPE
        # Allow environment override so container runs can choose model via OMI_MODEL/AIMO_QUANT
        env_model = os.getenv("OMI_MODEL") or os.getenv("AIMO_MODEL")
        env_quant = (
            os.getenv("MATHCODEORCHESTRATOR_QUANTIZATION")
            or os.getenv("OMI_QUANTIZATION")
            or os.getenv("AIMO_QUANTIZATION")
        )
        if model_name is None:
            model_name = env_model if env_model else config.HF_MODEL_NAME
        if quantization is None:
            # Legacy MATHCODEORCHESTRATOR_QUANTIZATION wins; else OMI_/AIMO_/default via config
            quantization = env_quant if env_quant else config.QUANTIZATION_DEFAULT

        # Use quantized model for memory efficiency
        self.quantization = quantization
        self.model_name = model_name

        # Tokenizer/model are expensive; only load if we actually fall back to local generation.
        self.tokenizer = None

        # Initialize model (lazy loading)
        self.model = None
        self.pipeline = None
        self.last_rate_limited = False
        self._llm_call_budget_cap = max(1, int(os.getenv("AIMO_LLM_CALL_CAP_PER_PROBLEM", "12")))
        self._llm_call_count = 0

    def reset_call_budget(self) -> None:
        """Reset per-problem LLM call budget and transient rate-limit flag."""
        self._llm_call_budget_cap = max(1, int(os.getenv("AIMO_LLM_CALL_CAP_PER_PROBLEM", "12")))
        self._llm_call_count = 0
        self.last_rate_limited = False

    def _consume_call_budget(self) -> Optional[str]:
        """Return error text if per-problem call budget is exceeded."""
        if self._llm_call_count >= self._llm_call_budget_cap:
            return (
                f"ERROR: LLM call budget exceeded "
                f"({self._llm_call_count}/{self._llm_call_budget_cap})"
            )
        self._llm_call_count += 1
        return None

    def _update_rate_limit_flag(self, text: Optional[str]) -> None:
        """Track whether any provider response indicates rate limiting in this solve."""
        if not isinstance(text, str):
            return
        s = text.upper()
        if "RESOURCE_EXHAUSTED" in s or "429" in s or "TOO MANY REQUESTS" in s:
            self.last_rate_limited = True

    def _ensure_tokenizer(self):
        """Lazy-load tokenizer only when local pipeline is used."""
        global _GLOBAL_LLM_TOKENIZER
        if _GLOBAL_LLM_TOKENIZER is None:
            _GLOBAL_LLM_TOKENIZER = self._get_tokenizer(self.model_name)
            if getattr(_GLOBAL_LLM_TOKENIZER, "pad_token_id", None) is None:
                _GLOBAL_LLM_TOKENIZER.pad_token_id = getattr(_GLOBAL_LLM_TOKENIZER, "eos_token_id", 0)
        self.tokenizer = _GLOBAL_LLM_TOKENIZER
        return self.tokenizer

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
            weight_dtype = _dtype_for_local_weights(quantization_config)
            logger.info(
                f"Loading model: {self.model_name} with {self.quantization} quantization..."
            )

            is_local = self._is_local_model_path(self.model_name)
            kw = dict(
                device_map="auto",
                trust_remote_code=True,
                quantization_config=quantization_config,
                dtype=weight_dtype,
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
        if self.quantization not in ("4bit", "8bit"):
            return None  # Full precision
        if BitsAndBytesConfig is None:
            logger.warning("transformers BitsAndBytesConfig unavailable; using full precision")
            return None
        try:
            import bitsandbytes  # noqa: F401
        except ImportError:
            logger.warning(
                "bitsandbytes not installed; using full precision instead of %s. "
                "Install: pip install -U bitsandbytes>=0.46.1, or set OMI_QUANTIZATION=none.",
                self.quantization,
            )
            return None
        if self.quantization == "4bit":
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=False,
            )
        # 8bit: GPU 메모리 부족 시 CPU로 일부 오프로드 허용 (32-bit 유지)
        enable_cpu_offload = os.getenv("AIMO_LLM_INT8_CPU_OFFLOAD", "1") == "1"
        return BitsAndBytesConfig(
            load_in_8bit=True,
            bnb_8bit_compute_dtype=torch.float16,
            llm_int8_enable_fp32_cpu_offload=enable_cpu_offload,
        )

    def _get_pipeline(self):
        """Get or create the text generation pipeline."""
        global _GLOBAL_LLM_PIPE
        if _GLOBAL_LLM_PIPE is None:
            self._ensure_tokenizer()
            model = self._get_model()
            logger.info("Setting up text generation pipeline...")
            pipe_dtype = _dtype_for_local_weights(self._get_quantization_config())

            # 생성 옵션은 generate() 호출 시에만 전달 (pipeline 생성 시 넣으면 호출 시와 중복되어 경고 발생)
            _GLOBAL_LLM_PIPE = pipeline(
                "text-generation",
                model=model,
                tokenizer=self.tokenizer,
                device_map="auto",
                dtype=pipe_dtype,
            )
            logger.info("Pipeline ready")
        return _GLOBAL_LLM_PIPE

    def generate(self, prompt: str, do_sample: bool = False, temperature: float = 0.1) -> str:
        """
        Generate code using local HuggingFace model or remote inference API.
        If OMI_REMOTE_INFERENCE_URL is set, calls that URL (computing engine = remote).
        """
        budget_err = self._consume_call_budget()
        if budget_err:
            logger.warning("%s", budget_err)
            return budget_err

        # 0) Vertex Endpoint (fine-tuned Qwen) if configured
        try:
            from .vertex_endpoint_inference import (
                is_vertex_endpoint_configured,
                predict_vertex_endpoint,
            )
            if is_vertex_endpoint_configured():
                if "MathCoder" in (self.model_name or ""):
                    formatted = f"### Problem:\n{prompt}\n\n### Solution:\n"
                else:
                    formatted = prompt
                out = predict_vertex_endpoint(formatted, temperature=temperature)
                self._update_rate_limit_flag(out)
                return out
        except Exception as e:
            logger.warning("Vertex endpoint inference check failed: %s", e)

        try:
            from .vertex_inference import (
                is_vertex_configured,
                generate_vertex,
                consume_vertex_rate_limit_signal,
            )
            if is_vertex_configured():
                if "MathCoder" in (self.model_name or ""):
                    formatted = f"### Problem:\n{prompt}\n\n### Solution:\n"
                else:
                    formatted = prompt
                out = generate_vertex(formatted, temperature=temperature)
                if consume_vertex_rate_limit_signal():
                    self.last_rate_limited = True
                self._update_rate_limit_flag(out)
                return out
            _log_vertex_skipped_once()
        except Exception as e:
            logger.warning("Vertex inference check failed: %s", e)

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
                out = generate_remote(formatted)
                self._update_rate_limit_flag(out)
                return out
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
            self._ensure_tokenizer()
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
            max_tokens = int(os.getenv("AIMO_MAX_NEW_TOKENS", "16384"))
            # GenerationConfig만 사용해 전달 (개별 인자와 중복 시 경고, max_length 미설정 시 pipeline 기본값 20과 충돌)
            # temperature는 일부 백엔드에서 무시되어 경고가 나오므로 생략 (do_sample만으로 샘플링 제어)
            gen_cfg_kw = dict(
                max_new_tokens=max_tokens,
                do_sample=do_sample,
                num_return_sequences=1,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                max_length=None,  # pipeline 기본 20과 충돌 방지
            )
            gen_config = GenerationConfig(**gen_cfg_kw)
            # pipeline은 GenerationConfig 객체를 받아야 함 (dict 전달 시 model_kwargs/bos_token_id 오류)
            # temperature 제거 후 다시 객체로 만들어 전달 (경고 방지)
            _gen_dict = gen_config.to_dict()
            _gen_dict.pop("temperature", None)
            _gen_dict = {k: v for k, v in _gen_dict.items() if v is not None}
            gen_config = GenerationConfig(**_gen_dict)

            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        message=".*(?:not valid|ignored).*temperature.*",
                        category=UserWarning,
                    )
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
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore",
                            message=".*(?:not valid|ignored).*temperature.*",
                            category=UserWarning,
                        )
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
        self._mock_solver = None
        if _aimo_fast_test_enabled():
            from .mock_solver import MockSolver

            self._mock_solver = MockSolver()
            self.llm = self._mock_solver.llm
        else:
            self.llm = LocalLLMClient()
        self.last_reasoning: Optional[str] = (
            None  # stores structured reasoning when used
        )
        self.last_syntax_error: bool = False

    def generate_code(self, problem_text: str, strategy: str) -> str:
        """Constructs prompt(s) and gets code from the LLM.
        If structured reasoning enabled, first obtain reasoning trace then code.
        """
        if self._mock_solver is not None:
            complexity_score = assess_complexity(problem_text)
            self.last_complexity_score = complexity_score
            return self._mock_solver.generate_code(problem_text, strategy)

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
        self, problem_text: str, strategy: str, num_candidates: int, _temps: list[float]
    ) -> list[str]:
        """Generate multiple candidate codes (sharing single reasoning) for voting.

        _temps: 현재 미사용 (호환성 유지용, orchestrator에서 CANDIDATE_TEMPS 전달).
        """
        if self._mock_solver is not None:
            complexity_score = assess_complexity(problem_text)
            self.last_complexity_score = complexity_score
            one = self._mock_solver.generate_code(problem_text, strategy)
            return [one for _ in range(max(1, num_candidates))]

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
            prompt = self._construct_prompt(
                problem_text,
                strategy,
                reasoning_text if use_structured else None,
                lemma_snippets,
            )
            try:
                generated_text = self.llm.generate(prompt, do_sample=True)
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
        On failure, returns ``print('ERROR: Code generation failed')`` so the
        executor surfaces a stable string (see logs / dashboard).
        """
        raw_in = response if isinstance(response, str) else ""
        # Budget / provider errors are returned as plain text, not Python.
        if isinstance(response, str) and response.strip().startswith("ERROR:"):
            self.last_syntax_error = False
            msg = response.strip()
            logger.warning("LLM returned error text instead of code: %s", msg[:300])
            return f"print({repr(msg)})"

        code = response.strip()

        # Normalize problematic Unicode whitespace that often appears in model output
        # and breaks Python parsing (e.g., NBSP U+00A0, BOM, zero-width spaces).
        code = (
            code.replace("\u00A0", " ")
            .replace("\u2007", " ")
            .replace("\u202F", " ")
            .replace("\u200B", "")
            .replace("\uFEFF", "")
        )

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
            if os.getenv("AIMO_LOG_FAILED_CODEGEN", "").strip().lower() in (
                "1",
                "true",
                "yes",
            ):
                logger.warning(
                    "AIMO_LOG_FAILED_CODEGEN: raw model output prefix (repr): %r",
                    raw_in[:1200],
                )
            self.last_syntax_error = True
            code = "print('ERROR: Code generation failed')"
        return code


# Note: Install transformers and sentencepiece if needed:
# pip install --upgrade transformers sentencepiece
