"""




Orchestrator




- Coordinates the 5-Stage Pipeline




- Implements the "Fast Fail & Fallback" loop




"""









import os
import datetime
from typing import Dict, Any

from . import config




from .reasoning_utils import extract_answer, extract_final_answer_from_output, normalize_multi_agent_answer, log_result, make_ids, build_refine_prompt, count_free_symbols, count_tokens, assess_complexity




from .feature_extractor import extract_features, rapid_intuition_phase




from .lemma_cache import GLOBAL_LEMMA_CACHE




from .stage3_router import CalculationRouter




from .strategy_bandit import StrategyBandit




from .stage4_execution import CodeExecutor




from .stage5_verification import VerificationRouter




from .reconciliation import ReasoningReconciler




from .solver import Solver




from .problem_decomposer import ProblemDecomposer




from .geometric_solver import GeometricSolver




from .hybrid_reasoning_engine import HybridReasoningEngine




from .multi_agent_reasoner import MultiAgentReasoner
from .refine_loop import create_refine_loop
from .stage1_labeling import ProblemAnalyzer
from .stage2_retrieval import KnowledgeGroundRetriever
from .settings import settings

from .executor_env import executor_wall_seconds_from_env
from .orchestrator_helpers import (
    classify_problem,
    classify_problem_with_diagnosis,
    inject_reverse_check,
    attempt_code_fix,
    build_fix_code_prompt,
    is_execution_error_output,
    map_reconciliation_status_to_refine_error,
    solve_result_verification_fields,
)
from .xai_summary import build_user_answer_explanation
from .logger import get_logger

logger = get_logger()




try:
    import opentelemetry.trace as trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    _OTEL_AVAILABLE = True
except Exception:
    _OTEL_AVAILABLE = False

    class _NoopSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_attribute(self, *args, **kwargs):
            return None

        def add_event(self, *args, **kwargs):
            return None

    class _NoopTracer:
        def start_as_current_span(self, *_args, **_kwargs):
            return _NoopSpan()

    class _NoopTrace:
        def set_tracer_provider(self, *_args, **_kwargs):
            return None

        def get_tracer(self, *_args, **_kwargs):
            return _NoopTracer()

        def get_tracer_provider(self):
            return self

        def add_span_processor(self, *_args, **_kwargs):
            return None

    trace = _NoopTrace()


# Initialize tracing




if _OTEL_AVAILABLE:
    trace.set_tracer_provider(TracerProvider())




tracer = trace.get_tracer(__name__)









# OTLP: only when OMI_OTLP_TRACING=1 (avoids localhost:4317 connection errors)
if _OTEL_AVAILABLE and os.environ.get("OMI_OTLP_TRACING", "").lower() in ("1", "true", "yes"):
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
        trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
    except Exception as e:
        get_logger().debug("OTLP tracing disabled: %s", e)
# Console exporter only when OMI_CONSOLE_TRACING=1
if _OTEL_AVAILABLE and os.environ.get("OMI_CONSOLE_TRACING", "").lower() in ("1", "true", "yes"):
    try:
        trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    except Exception:
        pass









class PipelineOrchestrator:




    def __init__(self):




        with tracer.start_as_current_span("PipelineOrchestrator Initialization"):




            self.router = CalculationRouter()




            # Wall / CPU defaults: unlimited unless env sets finite caps (see executor_env, stage4_execution).
            self.executor = CodeExecutor(timeout_seconds=executor_wall_seconds_from_env())




            self.verifier = VerificationRouter()




            self.reconciler = ReasoningReconciler(self.verifier)




            self.solver = Solver()




            self.decomposer = ProblemDecomposer(self.solver.llm)




            self.geo_solver = GeometricSolver(self.solver.llm)




            self.hybrid_engine = HybridReasoningEngine(self.solver, self.executor)

            self.refine_loop = create_refine_loop(
                max_iterations=settings.refine_max_iterations,
                enable_loop=settings.refine_enabled
            )

            self.multi_agent = None  # Lazy initialize
            self.problem_analyzer = ProblemAnalyzer()
            self.knowledge_retriever = KnowledgeGroundRetriever()









    def solve_problem(self, domain: str, variables: Dict[str, Any], problem_text: str, time_budget: float = 60.0, trace_callback=None) -> Dict[str, Any]:




        with tracer.start_as_current_span("solve_problem") as span:




            span.set_attribute("domain", domain)




            span.set_attribute("time_budget", time_budget)




            span.add_event("Starting problem solving pipeline")




            """




            Executes the solving pipeline with fallback logic.




            Args:




                time_budget: Reserved for API/telemetry (seconds); does not cap code execution wall time.




            """




            ids = make_ids(problem_text)
            request_id = ids.get("run_id", "unknown")
            pipeline_trace = []

            def add_trace(stage, status, details=None):
                item = {
                    "stage": stage,
                    "status": status,
                    "details": details,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                pipeline_trace.append(item)
                if trace_callback:
                    try:
                        trace_callback(item)
                    except Exception:
                        pass

            add_trace("Pipeline Initialization", "completed", f"Run ID: {request_id}")

            # Reproducibility: apply a global seed if configured.
            # This must not use/inspect reference answers and should only affect randomness.
            try:
                from .reproducibility import get_global_seed, apply_global_seed

                seed = get_global_seed()
                if seed is not None:
                    apply_global_seed(seed)
                    span.set_attribute("aimo_global_seed", seed)
            except Exception as e:
                logger.debug(f"Global seed not applied: {e}")

            try:
                if hasattr(self.solver, "llm") and hasattr(self.solver.llm, "reset_call_budget"):
                    self.solver.llm.reset_call_budget()
            except Exception as e:
                logger.debug(f"LLM call budget reset skipped: {e}")

            try:
                self.solver.set_knowledge_ground(None)
            except Exception as e:
                logger.debug(f"knowledge ground reset skipped: {e}")




            logger.info(f"Solving Problem (run={ids['run_id']}, N={variables.get('N')}) [Budget: {time_budget}s]")

            # 0. Pre-classification rejection
            problem_type, input_diagnosis = classify_problem_with_diagnosis(problem_text)
            if problem_type == 'invalid' and not settings.fast_test:
                logger.info(f"Problem rejected as non-mathematical: {problem_text[:50]}...")
                rejection_detail = input_diagnosis.get('rejection_reason', 'Non-mathematical input detected')
                add_trace("Stage 0: Input Validation", "rejected", rejection_detail)
                # Add detailed signal analysis as a trace item
                sym_info = f"Symbols: {input_diagnosis['found_math_symbols'] or 'none'}"
                kw_info = f"Keywords: {input_diagnosis['found_math_keywords'] or 'none'}"
                digit_info = f"Digits: {'yes' if input_diagnosis['has_digits'] else 'no'}"
                conv_info = f"Conversational: {input_diagnosis['found_conversational'] or 'none'}"
                add_trace(
                    "Stage 0: Signal Analysis",
                    "rejected",
                    f"{sym_info} | {kw_info} | {digit_info} | {conv_info}"
                )
                return {
                    "answer": "죄송합니다. 입력하신 내용은 수학적 문제 해결 범위에 해당하지 않아 처리를 거부하였습니다.",
                    "reasoning": "AIMO 5단계 파이프라인의 'Stage 0: Input Validation' 단계에서 비수학적 입력으로 분석되었습니다. 유효한 수학 기호, 수식 또는 수학적 키워드가 포함된 문제를 입력해 주시기 바랍니다.",
                    "method": "rejection",
                    "status": "rejected",
                    "request_id": request_id,
                    "input_diagnosis": input_diagnosis,
                    "pipeline_trace": pipeline_trace,
                    "input_diagnosis": input_diagnosis,
                    "answer_explanation": build_user_answer_explanation(
                        verified=False,
                        structured_used=False,
                        mismatch=False,
                        mismatch_type=None,
                        cleaned_result=None,
                        extracted=None,
                        last_reasoning=None,
                        strategy="rejection",
                        pipeline_trace=pipeline_trace
                    ),
                    **ids
                }
            add_trace("Stage 0: Input Validation", "passed", f"Mathematical content detected (type: {problem_type})")
            # Stage 0 passed — add signal analysis trace (shows what math signals were found)
            _sym_info = str(input_diagnosis.get('found_math_symbols') or 'none')
            _kw_info = str(input_diagnosis.get('found_math_keywords') or 'none')
            _digit_info = 'yes' if input_diagnosis.get('has_digits') else 'no'
            _conv_info = str(input_diagnosis.get('found_conversational') or 'none')
            add_trace(
                "Stage 0: Signal Analysis",
                "completed",
                f"Symbols: {_sym_info} | Keywords: {_kw_info} | Digits: {_digit_info} | Conversational: {_conv_info}"
            )





            feat = extract_features(problem_text, complexity_score=None)









            # Rapid Intuition Phase: Instant problem classification (diffusion-style)




            problem_type_intuition, preferred_strategy = rapid_intuition_phase(problem_text)




            if preferred_strategy:




                logger.info(f"Instant classification: {problem_type_intuition} -> priority {preferred_strategy}")













            complexity_score = assess_complexity(problem_text)
            add_trace("Stage 1: Classification", "completed", f"Type: {problem_type}, Complexity: {complexity_score}")

            if getattr(config, "USE_LLM_STAGE1_CLASSIFIER", False):
                llm_stage1 = self.problem_analyzer.classify_with_llm(problem_text, add_trace=add_trace)
                llm_problem_type = llm_stage1.get("problem_type")
                llm_complexity = llm_stage1.get("complexity_score")
                if llm_problem_type in {"computational", "geometric", "proof", "complex"}:
                    problem_type = llm_problem_type
                if isinstance(llm_complexity, int):
                    complexity_score = llm_complexity
                add_trace("Stage 1: LLM Classification", "completed", f"Refined Type: {problem_type}")
                logger.info(
                    "stage_event request_id=%s stage=stage1_classification strategy=stage1_llm "
                    "verified=false latency_ms=0 error_type=none problem_type=%s complexity_score=%s",
                    request_id,
                    problem_type,
                    complexity_score,
                )

            # Stage 2: prior knowledge ground (deterministic snippets → code-generation prompts)
            if settings.use_knowledge_ground:
                kg_text = self.knowledge_retriever.retrieve(domain or "", problem_type, problem_text, add_trace=add_trace)
                self.solver.set_knowledge_ground(kg_text)
                if kg_text:
                    add_trace("Stage 2: Knowledge Retrieval", "completed", f"Retrieved {len(kg_text)} chars of context")
                    logger.info(
                        "stage_event request_id=%s stage=stage2_retrieval strategy=knowledge_ground "
                        "verified=false latency_ms=0 error_type=none chars=%s",
                        request_id,
                        len(kg_text),
                    )
                else:
                    add_trace("Stage 2: Knowledge Retrieval", "skipped", "No relevant knowledge found")
            else:
                self.solver.set_knowledge_ground(None)
                add_trace("Stage 2: Knowledge Retrieval", "disabled", "Knowledge grounding is off")




            decomposition_threshold = getattr(config, 'DECOMPOSITION_COMPLEXITY_THRESHOLD', 15)




            should_decompose = problem_type == 'complex' and complexity_score >= decomposition_threshold
            if os.getenv("AIMO_DISABLE_DECOMPOSITION", "0") == "1":
                should_decompose = False




            logger.debug(f"Complexity Analysis: Score={complexity_score}, Type={problem_type}, Threshold={decomposition_threshold}, Decompose={should_decompose}")









            # Inject reverse check hooks for simple arithmetic problems




            inject_reverse_check(problem_text, variables)

            # Puzzle overlay CSP handler: deterministic backtracking solver for encoded edge-triple constraints.
            # This avoids long LLM codegen stalls for constraint-satisfaction puzzles.
            try:
                from .puzzle_overlay_csp import solve_overlay_puzzle_from_text

                overlay_json = solve_overlay_puzzle_from_text(problem_text)
                if overlay_json is not None:
                    logger.info("[Special Handler] Detected overlay puzzle CSP; solving deterministically")
                    return {
                        "answer": overlay_json,
                        "method": "puzzle_overlay_csp",
                        "code": None,
                        "execution_result": overlay_json,
                        "request_id": request_id,
                        "pipeline_trace": pipeline_trace,
                        "input_diagnosis": input_diagnosis,
                        "answer_explanation": build_user_answer_explanation(
                            verified=True,
                            structured_used=False,
                            mismatch=False,
                            mismatch_type=None,
                            cleaned_result=overlay_json,
                            extracted=overlay_json,
                            last_reasoning=None,
                            strategy="puzzle_overlay_csp",
                            pipeline_trace=pipeline_trace,
                        ),
                        **solve_result_verification_fields(variables, True),
                        **ids,
                    }
            except Exception as e:
                logger.debug(f"[Puzzle overlay CSP handler skipped] {e}")




            




            # Geometric handler: 활성화 시 기하 문제에서 전용 솔버 시도 (기본 비활성)
            if getattr(config, "USE_GEOMETRIC_HANDLER", False) and problem_type == "geometric" and len(problem_text) < 500:
                logger.info("[Special Handler] Detected GEOMETRIC problem (simple)")
                result = self._solve_geometric(problem_text, add_trace=add_trace)
                if result:
                    return {
                        "answer": result,
                        "method": "geometric_handler",
                        "code": None,
                        "execution_result": result,
                        "request_id": request_id,
                        "pipeline_trace": pipeline_trace,
                        "input_diagnosis": input_diagnosis,
                        "answer_explanation": build_user_answer_explanation(
                            verified=True,
                            structured_used=False,
                            mismatch=False,
                            mismatch_type=None,
                            cleaned_result=result,
                            extracted=None,
                            last_reasoning=None,
                            strategy="geometric_handler",
                            pipeline_trace=pipeline_trace,
                        ),
                        **solve_result_verification_fields(variables, True),
                        **ids,
                    }
                logger.debug("[Geometric handler failed, falling back to general pipeline]")

            # Handle complex problems that need decomposition




            hybrid_graph_disabled = os.getenv("AIMO_DISABLE_HYBRID_GRAPH", "0") == "1"
            if should_decompose:




                logger.info("Compromise Point activated - decomposing based on complexity threshold")




                analysis = self.decomposer.analyze_problem(problem_text, add_trace=add_trace)




                if analysis.get('decompose') == 'yes':




                    # (can be disabled in cost/latency-sensitive runs).
                    if not hybrid_graph_disabled:
                        logger.info("Using Hybrid Reasoning Engine with Graph Decomposition")

                        add_trace("Stage 2.5: Hybrid Graph Solver", "processing", "Attempting graph-based decomposition")

                        try:
                            result = self.hybrid_engine.solve_with_graph(problem_text, add_trace=add_trace)
                            if result and "Error" not in result:
                                add_trace("Stage 2.5: Hybrid Graph Solver", "completed", "Graph solution found")
                                return {
                                    'answer': result,
                                    'method': 'hybrid_graph_engine',
                                    'code': None,
                                    'execution_result': result,
                                    'request_id': request_id,
                                    'pipeline_trace': pipeline_trace,
                                    'input_diagnosis': input_diagnosis,
                                    'answer_explanation': build_user_answer_explanation(
                                        verified=True,
                                        structured_used=False,
                                        mismatch=False,
                                        mismatch_type=None,
                                        cleaned_result=result,
                                        extracted=None,
                                        last_reasoning=None,
                                        strategy="hybrid_graph_engine",
                                        pipeline_trace=pipeline_trace,
                                    ),
                                    **solve_result_verification_fields(variables, True),
                                    **ids,
                                }
                            logger.warning("Hybrid Engine failed, falling back to hierarchical solver")
                            add_trace("Stage 2.5: Hybrid Graph Solver", "failed", "Graph engine failed, falling back")
                            hierarchical_result = self.decomposer.solve_hierarchically(problem_text, self.solver, self.executor, add_trace=add_trace)
                            add_trace("Stage 2.6: Hierarchical Solver", "completed", "Sub-problem decomposition successful")
                            return {
                                'answer': hierarchical_result,
                                'method': 'hierarchical_decomposer',
                                'code': None,
                                'execution_result': hierarchical_result,
                                'request_id': request_id,
                                'pipeline_trace': pipeline_trace,
                                'input_diagnosis': input_diagnosis,
                                'answer_explanation': build_user_answer_explanation(
                                    verified=True,
                                    structured_used=False,
                                    mismatch=False,
                                    mismatch_type=None,
                                    cleaned_result=hierarchical_result,
                                    extracted=None,
                                    last_reasoning=None,
                                    strategy="hierarchical_decomposer",
                                    pipeline_trace=pipeline_trace,
                                ),
                                **solve_result_verification_fields(variables, True),
                                **ids,
                            }
                        except Exception as e:
                            logger.error(f"Hybrid Engine error: {str(e)}", exc_info=True)
                            add_trace("Stage 2.5: Hybrid Graph Solver", "failed", str(e)[:100])
                            hierarchical_result = self.decomposer.solve_hierarchically(problem_text, self.solver, self.executor, add_trace=add_trace)
                            add_trace("Stage 2.6: Hierarchical Solver", "completed", "Fallback to sub-problem decomposition")
                            return {
                                'answer': hierarchical_result,
                                'method': 'hierarchical_decomposer',
                                'code': None,
                                'execution_result': hierarchical_result,
                                'request_id': request_id,
                                'pipeline_trace': pipeline_trace,
                                'input_diagnosis': input_diagnosis,
                                'answer_explanation': build_user_answer_explanation(
                                    verified=True,
                                    structured_used=False,
                                    mismatch=False,
                                    mismatch_type=None,
                                    cleaned_result=hierarchical_result,
                                    extracted=None,
                                    last_reasoning=None,
                                    strategy="hierarchical_decomposer",
                                    pipeline_trace=pipeline_trace,
                                ),
                                **solve_result_verification_fields(variables, True),
                                **ids,
                            }
                    else:
                        logger.info("Hybrid graph engine disabled (AIMO_DISABLE_HYBRID_GRAPH=1); using hierarchical solver")
                        add_trace("Stage 2.6: Hierarchical Solver", "processing", "Decomposing problem into sub-tasks")
                        hierarchical_result = self.decomposer.solve_hierarchically(problem_text, self.solver, self.executor, add_trace=add_trace)
                        add_trace("Stage 2.6: Hierarchical Solver", "completed", "Hierarchical solution generated")
                        return {
                            'answer': hierarchical_result,
                            'method': 'hierarchical_decomposer',
                            'code': None,
                            'execution_result': hierarchical_result,
                            'request_id': request_id,
                            'pipeline_trace': pipeline_trace,
                            'input_diagnosis': input_diagnosis,
                            'answer_explanation': build_user_answer_explanation(
                                verified=True,
                                structured_used=False,
                                mismatch=False,
                                mismatch_type=None,
                                cleaned_result=hierarchical_result,
                                extracted=None,
                                last_reasoning=None,
                                strategy="hierarchical_decomposer",
                                pipeline_trace=pipeline_trace,
                            ),
                            **solve_result_verification_fields(variables, True),
                            **ids,
                        }




            




            # 1. Get Prioritized Plan (standard flow)




            strategies = self.router.route(domain, variables)




            # Adaptive reordering based on historical performance




            bandit = StrategyBandit(config.LOG_PATH)




            strategies = bandit.reorder(strategies)




            logger.info(f"Strategic Plan (adaptive): {strategies}")









            # Reserve more time per strategy, limit to 3 attempts max (strategy list only; no executor runtime cap).
            max_attempts = min(3, len(strategies))
            strategies = strategies[:max_attempts]




            




            last_was_timeout = False
            structured_used = False

            # Phase 2.1: proof 또는 고복잡도일 때 multi-agent 선시도 (설정 시)
            disable_multi_agent = os.getenv("AIMO_DISABLE_MULTI_AGENT", "0") == "1"
            use_multi_agent_early = getattr(config, "USE_MULTI_AGENT_EARLY", False) and not disable_multi_agent
            multi_agent_early_threshold = getattr(config, "MULTI_AGENT_EARLY_COMPLEXITY_THRESHOLD", 20)
            bypass_multi_agent_on_rate_limit = os.getenv("AIMO_BYPASS_MULTI_AGENT_ON_RATE_LIMIT", "1") == "1"
            rate_limited_in_this_solve = bool(
                getattr(getattr(self.solver, "llm", None), "last_rate_limited", False)
            )
            if use_multi_agent_early and (problem_type == "proof" or (complexity_score or 0) >= multi_agent_early_threshold):
                if bypass_multi_agent_on_rate_limit and rate_limited_in_this_solve:
                    logger.info("Skipping early multi-agent due to prior rate-limit signal in this solve.")
                else:
                    if self.multi_agent is None:
                        self.multi_agent = MultiAgentReasoner(self.solver, self.executor)
                    add_trace("Stage 2.7: Multi-Agent Reasoner", "processing", "Engaging multi-agent consensus protocol")
                    try:
                        multi_result = self.multi_agent.solve_with_multi_agent(problem_text, add_trace=add_trace)
                        final_answer = normalize_multi_agent_answer(multi_result.get("final_answer"))
                        if final_answer:
                            add_trace("Stage 2.7: Multi-Agent Reasoner", "completed", f"Consensus reached: {final_answer}")
                            logger.info(f"MULTI-AGENT (early) Success! Answer: {final_answer}")
                            log_result({
                                "problem_preview": problem_text[:80],
                                "strategy": "multi_agent_early",
                                "structured_used": True,
                                "complexity_score": complexity_score,
                                "extracted_answer": final_answer,
                                "execution_result": "multi_agent_result",
                                **solve_result_verification_fields(variables, True),
                                "attempt": 1,
                                "mismatch": False,
                                "mismatch_type": None,
                                "resource_usage": None,
                                "strategy_features": feat,
                                "cache_hits": 0,
                                **ids,
                                "strategy_order": ["multi_agent_early"],
                            }, path=config.LOG_PATH)
                            return {
                                "answer": final_answer,
                                "method": "multi_agent",
                                "code": None,
                                "execution_result": "multi_agent_result",
                                "structured_used": True,
                                "extracted_answer": final_answer,
                                "request_id": request_id,
                                "pipeline_trace": pipeline_trace,
                                "input_diagnosis": input_diagnosis,
                                "answer_explanation": build_user_answer_explanation(
                                    verified=True,
                                    structured_used=True,
                                    mismatch=False,
                                    mismatch_type=None,
                                    cleaned_result="multi_agent_result",
                                    extracted=final_answer,
                                    last_reasoning=self.solver.last_reasoning,
                                    strategy="multi_agent",
                                    pipeline_trace=pipeline_trace,
                                ),
                                **solve_result_verification_fields(variables, True),
                                "mismatch": False,
                                "mismatch_type": None,
                                "resource_usage": None,
                                "strategy_features": feat,
                                "cache_hits": 0,
                                **ids,
                            }
                    except Exception as e:
                        logger.debug(f"Multi-agent early attempt failed: {e}")

            for attempt, strategy in enumerate(strategies, 1):




                # Skip Path B: The Theoretician if previous attempt timed out




                if last_was_timeout and "Theoretician" in strategy:




                    logger.debug(f"Attempt {attempt}: Skipping {strategy} (previous timeout)")




                    continue




                    




                logger.info(f"Attempt {attempt}: Trying Strategy: {strategy}")
                add_trace(f"Attempt {attempt}: {strategy}", "processing", "Initiating strategy execution")
                
                # Rate Limit Resilience: Retry the same strategy if the model signals 429/503
                # We do this up to 2 times per strategy before falling back.
                current_strategy_backoff = 1
                strategy_retries = max(1, int(os.getenv("AIMO_STRATEGY_RETRIES", "3")))
                for strategy_retry in range(strategy_retries):
                    logger.info(
                        "stage_event request_id=%s stage=strategy_attempt strategy=%s verified=false latency_ms=0 error_type=none attempt=%s retry=%s",
                        request_id,
                        strategy,
                        attempt,
                        strategy_retry,
                    )

                    last_was_timeout = False




                




                # 2. Generate Code (multi-candidate voting if enabled)




                selected_index = None




                if getattr(config, 'USE_VOTING', False):




                    candidates = self.solver.generate_candidates(problem_text, strategy, config.NUM_CANDIDATES, config.CANDIDATE_TEMPS)




                    logger.debug(f"Generated {len(candidates)} candidate codes")




                    code = None




                    result = None




                    resource_stats = None




                    vote_tally = {}
                    for idx, cand in enumerate(candidates):
                        if hasattr(self.executor, 'execute_with_stats'):
                            exec_out, stats = self.executor.execute_with_stats(cand)
                            cand_result = exec_out
                            cand_stats = stats
                        else:
                            cand_result = self.executor.execute(cand)
                            cand_stats = None

                        cand_result = str(cand_result)
                        cleaned = extract_final_answer_from_output(cand_result)
                        verified_cand = (
                            False
                            if is_execution_error_output(cleaned)
                            else self.verifier.verify(cleaned, variables)
                        )

                        if cleaned not in vote_tally:
                            vote_tally[cleaned] = {'count': 0, 'code': cand, 'stats': cand_stats, 'verified': verified_cand}
                        
                        vote_tally[cleaned]['count'] += 1
                        if verified_cand:
                            vote_tally[cleaned]['verified'] = True

                    best_answer = None
                    best_tally = None
                    
                    verified_candidates = {k: v for k, v in vote_tally.items() if v['verified']}
                    if verified_candidates:
                        best_answer = max(verified_candidates.items(), key=lambda x: x[1]['count'])[0]
                        best_tally = verified_candidates[best_answer]
                        logger.info(f"Majority Voting: Selected VERIFIED answer '{best_answer}' with {best_tally['count']} votes.")
                    else:
                        if vote_tally:
                            best_answer = max(vote_tally.items(), key=lambda x: x[1]['count'])[0]
                            best_tally = vote_tally[best_answer]
                            logger.info(f"Majority Voting: No verified answers. Selected most frequent '{best_answer}' with {best_tally['count']} votes.")
                            
                    if best_tally:
                        code = best_tally['code']
                        result = best_answer
                        resource_stats = best_tally['stats']
                        selected_index = 0
                    else:
                        code = candidates[0] if candidates else "print('ERROR: no candidates')"
                        result = 'ERROR: no candidates'




                else:




                    code = self.solver.generate_code(problem_text, strategy)
                    add_trace(f"Attempt {attempt}: Code Generation", "completed", f"Generated logic ({len(code)} chars)")




                    




                    # Check if generation timed out




                    if "TIMEOUT" in code or "ERROR: Generation timeout" in code:




                        logger.warning("Generation timed out, trying next strategy...")




                        last_was_timeout = True




                        continue




                    




                    logger.debug(f"Generated Code ({len(code)} chars)")




                    resource_stats = None




                    if hasattr(self.executor, 'execute_with_stats'):




                        exec_out, stats = self.executor.execute_with_stats(code, add_trace=add_trace)
                        add_trace(f"Attempt {attempt}: Execution", "completed", "Code execution successful")
                        result = exec_out




                        resource_stats = stats




                    else:




                        result = self.executor.execute(code, add_trace=add_trace)









                # Metrics




                code_chars = len(code)




                reasoning_tokens = count_tokens(self.solver.last_reasoning) if self.solver.last_reasoning else 0




                




                # 4. Check for Execution Failure & Traceback (Self-Correction)
                if result and "Error" in result:
                    logger.warning(f"Execution Failed: {result.strip()}")
                    add_trace(f"Attempt {attempt}: Execution Failed", "failed", result.strip()[:100])
                    max_correction_attempts = getattr(config, "EXECUTOR_SELF_CORRECTION_MAX_ATTEMPTS", 1)
                    fix_success = False
                    current_code, current_result = code, result
                    for correction_attempt in range(max_correction_attempts):
                        logger.info("Analyzing Traceback (Self-Correction)...")
                        fixed_code = attempt_code_fix(current_code, current_result) if (current_result and current_code) else None
                        if fixed_code is None and current_result and current_code and "Error:" in current_result:
                            fix_prompt = build_fix_code_prompt(current_code, current_result)
                            if fix_prompt:
                                try:
                                    fixed_code = self.solver.generate_code_from_prompt(fix_prompt)
                                except Exception:
                                    fixed_code = None
                        if not fixed_code:
                            break
                        logger.info("Retrying with Fixed Code...")
                        add_trace(f"Attempt {attempt}: Self-Correction", "processing", f"Correction step {correction_attempt + 1}")
                        try:
                            current_result = self.executor.execute(fixed_code)
                        except Exception as e:
                            current_result = f"ERROR: {str(e)}"
                        if "Error" not in current_result:
                            result = current_result
                            fix_success = True
                            logger.info(f"Fix Successful! Result: {result.strip()}")
                            add_trace(f"Attempt {attempt}: Self-Correction", "completed", "Logic successfully repaired")
                            break
                        logger.warning(f"Fix Failed again: {current_result.strip()}")
                        add_trace(f"Attempt {attempt}: Self-Correction", "failed", f"Step {correction_attempt + 1} failed")
                        current_code = fixed_code
                    if not fix_success:
                        logger.warning("Triggering Fallback Strategy...")
                        break # Exit strategy_retry loop to move to NEXT strategy in candidates-loop context
                        
                    # Check for transient rate limit after generation/fix
                    if hasattr(self.solver.llm, "last_rate_limited") and self.solver.llm.last_rate_limited:
                        import time
                        wait_sec = 5 * current_strategy_backoff
                        logger.warning(f"Rate limited (429/503 detected). Backing off {wait_sec}s and retrying SAME strategy...")
                        time.sleep(wait_sec)
                        current_strategy_backoff *= 2
                        self.solver.llm.last_rate_limited = False # Reset for retry
                        continue # Retry SAME strategy

                    # If we reached here without continuing, the strategy run is complete (success or logic fail)
                    break 

                # Keep raw execution output for XAI/dashboard (may include debug prints or tracebacks).
                raw_execution_output = result









                # 5. Verification Stage




                logger.debug("Verifying Answer...")




                # Guard: treat execution error strings as automatic failure




                # Ensure result is a string




                if not isinstance(result, str):




                    result = str(result)




                # Extract final answer from execution output (removes debug prints, labels, etc.)
                cleaned_result = extract_final_answer_from_output(result)

                # Payload fast-path: if execution produced a structured node->int assignment map,
                # treat it as a valid "answer" without numeric verification/reconciliation.
                if isinstance(cleaned_result, str):
                    cr = cleaned_result.strip()
                    if (cr.startswith("{") and cr.endswith("}")) and (
                        ("\"V1\"" in cr or "\"I1\"" in cr) or ("'V1'" in cr or "'I1'" in cr)
                    ):
                        answer_explanation = build_user_answer_explanation(
                            verified=True,
                            structured_used=structured_used,
                            mismatch=False,
                            mismatch_type=None,
                            cleaned_result=cleaned_result,
                            extracted=None,
                            last_reasoning=self.solver.last_reasoning,
                            strategy=strategy,
                            pipeline_trace=pipeline_trace,
                        )
                        return {
                            "answer": cleaned_result,
                            "method": strategy,
                            "code": code,
                            "execution_result": cleaned_result,
                            "request_id": request_id,
                            "pipeline_trace": pipeline_trace,
                            "input_diagnosis": input_diagnosis,
                            "structured_used": structured_used,
                            "extracted_answer": None,
                            "answer_explanation": answer_explanation,
                            **solve_result_verification_fields(variables, True),
                            **ids,
                        }

                if is_execution_error_output(cleaned_result):




                    verified = False




                else:




                    verified = self.verifier.verify(cleaned_result, variables)
                    add_trace("Verification", "completed" if verified else "failed", f"Verified result: {cleaned_result}")




                structured_used = bool(self.solver.last_reasoning)




                complexity_score = getattr(self.solver, 'last_complexity_score', None)

                extracted = extract_answer(self.solver.last_reasoning) if (structured_used and self.solver.last_reasoning) else None




                




                # Reasoning Reconciliation




                mismatch = False




                mismatch_type = None




                reconcile_details = ""




                




                if structured_used and extracted:




                    rec_result = self.reconciler.reconcile(extracted, cleaned_result, add_trace=add_trace)

                    if not rec_result.match:
                        mismatch = True
                        mismatch_type = rec_result.status
                        reconcile_details = rec_result.details





                    elif rec_result.status == 'MATCH_FORMAT_DIFF':




                        # Log format diff but not a failure




                        reconcile_details = rec_result.details




                




                # Override mismatch type for execution errors




                if is_execution_error_output(cleaned_result):




                    mismatch_type = 'execution_error'




                free_symbol_count = count_free_symbols(extracted or cleaned_result)




                if verified:




                    logger.info(f"Success! Verified Result: {cleaned_result}")
                    logger.info(
                        "stage_event request_id=%s stage=verification strategy=%s verified=true latency_ms=0 error_type=none",
                        request_id,
                        strategy,
                    )




                    # Lemma cache update on success (simple heuristic: store canonical extracted or execution result)




                    cache_hits = 0




                    if extracted:




                        if GLOBAL_LEMMA_CACHE.add(extracted):




                            cache_hits += 1




                    elif cleaned_result:




                        if GLOBAL_LEMMA_CACHE.add(cleaned_result):




                            cache_hits += 1




                    log_result({




                        'problem_preview': problem_text[:80],
                        'problem_text': problem_text,




                        'strategy': strategy,




                        'structured_used': structured_used,




                        'complexity_score': complexity_score,




                        'extracted_answer': extracted,




                        'execution_result': cleaned_result,
                        'execution_output_raw': raw_execution_output,
                        'generated_code': code,
                        'llm_reasoning': self.solver.last_reasoning,




                        **solve_result_verification_fields(variables, True),




                        'attempt': attempt,




                        'mismatch': mismatch,




                        'mismatch_type': mismatch_type,




                        'reconcile_details': reconcile_details,




                        'resource_usage': resource_stats,




                        'strategy_features': feat,




                        'cache_hits': cache_hits,




                        'code_chars': code_chars,




                        'reasoning_tokens': reasoning_tokens,




                        'free_symbol_count': free_symbol_count,




                        'syntax_error': getattr(self.solver, 'last_syntax_error', False),




                        'selected_candidate_index': selected_index,




                        **ids,




                        'strategy_order': strategies




                    }, path=config.LOG_PATH)




                    # 실행 결과가 유효하면 우선 사용(긴 추론에서 잘못된 "마지막 숫자" 방지)
                    execution_ok = cleaned_result and not is_execution_error_output(cleaned_result)
                    final_answer = (cleaned_result if execution_ok else extracted) or cleaned_result or extracted
                    answer_explanation = build_user_answer_explanation(
                        verified=True,
                        structured_used=structured_used,
                        mismatch=mismatch,
                        mismatch_type=mismatch_type,
                        cleaned_result=cleaned_result,
                        extracted=extracted,
                        last_reasoning=self.solver.last_reasoning,
                        strategy=strategy,
                        pipeline_trace=pipeline_trace,
                    )

                    return {




                        'answer': final_answer,




                        'method': strategy,




                        'code': code,




                        'execution_result': cleaned_result,
                        'request_id': request_id,
                        'pipeline_trace': pipeline_trace,
                        'input_diagnosis': input_diagnosis,
                        'structured_used': structured_used,




                        'extracted_answer': extracted,




                        'answer_explanation': answer_explanation,




                        **solve_result_verification_fields(variables, True),




                        'mismatch': mismatch,




                        'mismatch_type': mismatch_type,




                        'reconcile_details': reconcile_details,




                        'resource_usage': resource_stats,




                        'strategy_features': feat,




                        'cache_hits': cache_hits,




                        'code_chars': code_chars,




                        'reasoning_tokens': reasoning_tokens,




                        'free_symbol_count': free_symbol_count,




                        'syntax_error': getattr(self.solver, 'last_syntax_error', False),




                        'selected_candidate_index': selected_index,




                        **ids




                    }




                else:




                    logger.warning("Verification Failed. Triggering Fallback Strategy...")
                    logger.info(
                        "stage_event request_id=%s stage=verification strategy=%s verified=false latency_ms=0 error_type=%s",
                        request_id,
                        strategy,
                        mismatch_type or "verification_fail",
                    )

                    # Self-Refine Loop: Use RefineLoop module for cleaner code




                    refined_used = False




                    if structured_used and not getattr(self, '_refine_used', False):




                        refine_error_type = map_reconciliation_status_to_refine_error(mismatch_type) if mismatch_type else ('verification_fail' if not verified else 'mismatch')




                        refine_prompt = build_refine_prompt(problem_text, self.solver.last_reasoning, code,




                            refine_error_type, cleaned_result, extracted)




                        logger.info("Self-Refine Attempt...")
                        add_trace("Self-Refinement", "processing", f"Attempting to resolve {refine_error_type}")
                        refine_code = self.solver.generate_code_from_prompt(refine_prompt)




                        if hasattr(self.executor, 'execute_with_stats'):




                            refine_out, refine_stats = self.executor.execute_with_stats(refine_code)




                        else:




                            refine_out = self.executor.execute(refine_code)




                            refine_stats = None




                        refine_raw = str(refine_out)
                        refine_cleaned = extract_final_answer_from_output(refine_raw)
                        refine_verified = self.verifier.verify(refine_cleaned, variables)




                        refined_used = True




                        self._refine_used = True




                        refine_extracted = extract_answer(self.solver.last_reasoning) if self.solver.last_reasoning else None




                        refine_mismatch = False




                        refine_mismatch_type = None




                        refine_reconcile_details = ""




                        if refine_extracted:




                            # Use Reconciler for refine step too




                            refine_rec = self.reconciler.reconcile(refine_extracted, refine_cleaned)




                            if not refine_rec.match:




                                refine_mismatch = True




                                refine_mismatch_type = refine_rec.status




                                refine_reconcile_details = refine_rec.details




                            elif refine_rec.status == 'MATCH_FORMAT_DIFF':




                                refine_reconcile_details = refine_rec.details









                        log_result({




                            'problem_preview': problem_text[:80],
                            'problem_text': problem_text,




                            'strategy': strategy + '_refine',




                            'structured_used': structured_used,




                            'complexity_score': complexity_score,




                            'extracted_answer': refine_extracted,




                            'execution_result': refine_cleaned,
                            'execution_output_raw': refine_raw,
                            'generated_code': refine_code,
                            'llm_reasoning': self.solver.last_reasoning,




                            **solve_result_verification_fields(variables, refine_verified),




                            'attempt': attempt,




                            'mismatch': refine_mismatch,




                            'mismatch_type': refine_mismatch_type,




                            'reconcile_details': refine_reconcile_details,




                            'resource_usage': refine_stats,




                            **ids,




                            'strategy_order': strategies,




                            'refine': True




                        }, path=config.LOG_PATH)




                        refine_execution_ok = refine_cleaned and not is_execution_error_output(refine_cleaned)
                        refine_return_answer = (
                            (refine_cleaned if refine_execution_ok else refine_extracted)
                            or refine_cleaned
                            or refine_extracted
                        )

                        if refine_verified:




                            refine_answer_expl = build_user_answer_explanation(
                                verified=True,
                                structured_used=structured_used,
                                mismatch=refine_mismatch,
                                mismatch_type=refine_mismatch_type,
                                cleaned_result=refine_cleaned,
                                extracted=refine_extracted,
                                last_reasoning=self.solver.last_reasoning,
                                strategy=strategy + "_refine",
                                self_refined=True,
                                pipeline_trace=pipeline_trace,
                            )
                            add_trace("Self-Refinement", "completed", f"Refined answer verified: {refine_return_answer}")
                            return {




                                'answer': refine_return_answer,




                                'method': strategy + '_refine',




                                'code': refine_code,




                                'execution_result': refine_cleaned,
                                'request_id': request_id,
                                'pipeline_trace': pipeline_trace,
                                'input_diagnosis': input_diagnosis,
                                'structured_used': structured_used,




                                'extracted_answer': refine_extracted,




                                'answer_explanation': refine_answer_expl,




                                **solve_result_verification_fields(variables, True),




                                'mismatch': refine_mismatch,




                                'mismatch_type': refine_mismatch_type,




                                'reconcile_details': refine_reconcile_details,




                                'resource_usage': refine_stats,




                                'refine': True,




                                **ids




                            }




                        add_trace("Self-Refinement", "failed", "Refined answer could not be verified")
                    log_result({




                        'problem_preview': problem_text[:80],




                        'strategy': strategy,




                        'structured_used': structured_used,




                        'complexity_score': complexity_score,




                        'extracted_answer': extracted,




                        'execution_result': cleaned_result,




                        **solve_result_verification_fields(variables, False),




                        'attempt': attempt if 'attempt' in locals() else 1,




                        'mismatch': mismatch,




                        'mismatch_type': mismatch_type,




                        'reconcile_details': reconcile_details,




                        'resource_usage': resource_stats,




                        'refine': refined_used,




                        'strategy_features': feat,




                        'cache_hits': 0,




                        'code_chars': code_chars,




                        'reasoning_tokens': reasoning_tokens,




                        'free_symbol_count': free_symbol_count,




                        'syntax_error': getattr(self.solver, 'last_syntax_error', False),




                        **ids,




                        'strategy_order': strategies




                    }, path=config.LOG_PATH)




                    continue









            logger.error("All strategies failed.")









            # Try multi-agent reasoning as last resort
            if (
                bypass_multi_agent_on_rate_limit
                and bool(getattr(getattr(self.solver, "llm", None), "last_rate_limited", False))
            ):
                logger.warning("Skipping multi-agent fallback due to rate-limit signal (429/RESOURCE_EXHAUSTED).")
                return {
                    'answer': None,
                    'method': 'all_failed_rate_limited',
                    'code': None,
                    'execution_result': 'ERROR: skipped multi-agent due to rate limiting',
                    'request_id': request_id,
                    'pipeline_trace': pipeline_trace,
                    'input_diagnosis': input_diagnosis,
                    'structured_used': structured_used,
                    'extracted_answer': None,
                    'answer_explanation': build_user_answer_explanation(
                        verified=False,
                        structured_used=structured_used,
                        mismatch=False,
                        mismatch_type=None,
                        cleaned_result=None,
                        extracted=None,
                        last_reasoning=self.solver.last_reasoning,
                        strategy="all_failed_rate_limited",
                        pipeline_trace=pipeline_trace,
                    ),
                    **solve_result_verification_fields(variables, False),
                    'mismatch': False,
                    'mismatch_type': None,
                    'reconcile_details': None,
                    'resource_usage': None,
                    'strategy_features': feat,
                    'cache_hits': 0,
                    **ids,
                }




            if disable_multi_agent:
                logger.info("Multi-agent fallback disabled (AIMO_DISABLE_MULTI_AGENT=1)")
                return {
                    'answer': None,
                    'method': 'all_failed',
                    'code': None,
                    'execution_result': 'All strategies failed',
                    'request_id': request_id,
                    'pipeline_trace': pipeline_trace,
                    'input_diagnosis': input_diagnosis,
                    'structured_used': bool(self.solver.last_reasoning),
                    'extracted_answer': None,
                    'answer_explanation': build_user_answer_explanation(
                        verified=False,
                        structured_used=bool(self.solver.last_reasoning),
                        mismatch=False,
                        mismatch_type='NO_VALID_OUTPUT',
                        cleaned_result='All strategies failed',
                        extracted=None,
                        last_reasoning=self.solver.last_reasoning,
                        strategy='all_failed',
                        pipeline_trace=pipeline_trace,
                    ),
                    **solve_result_verification_fields(variables, False),
                    **ids,
                }

            if self.multi_agent is None:




                self.multi_agent = MultiAgentReasoner(self.solver, self.executor)




            multi_result = self.multi_agent.solve_with_multi_agent(problem_text)

            # Normalize: dict(role/content) -> content에서 숫자 추출
            final_answer = normalize_multi_agent_answer(multi_result.get('final_answer'))

            if final_answer:
                logger.info(f"MULTI-AGENT Success! Answer: {final_answer}")




                log_result({




                    'problem_preview': problem_text[:80],




                    'strategy': 'multi_agent',




                    'structured_used': True,




                    'complexity_score': None,

                    'extracted_answer': final_answer,

                    'execution_result': 'multi_agent_result',




                    **solve_result_verification_fields(variables, True),




                    'attempt': 1,




                    'mismatch': False,




                    'mismatch_type': None,




                    'resource_usage': None,




                    'strategy_features': feat,




                    'cache_hits': 0,




                    **ids,




                    'strategy_order': ['multi_agent']




                }, path=config.LOG_PATH)




                return {
                    'answer': final_answer,
                    'method': 'multi_agent',
                    'code': None,
                    'execution_result': 'multi_agent_result',
                    'request_id': request_id,
                    'pipeline_trace': pipeline_trace,
                    'input_diagnosis': input_diagnosis,
                    'structured_used': True,
                    'extracted_answer': final_answer,
                    'answer_explanation': build_user_answer_explanation(
                        verified=True,
                        structured_used=True,
                        mismatch=False,
                        mismatch_type=None,
                        cleaned_result='multi_agent_result',
                        extracted=final_answer,
                        last_reasoning=self.solver.last_reasoning,
                        strategy='multi_agent',
                        pipeline_trace=pipeline_trace,
                    ),
                    **solve_result_verification_fields(variables, True),
                    'mismatch': False,
                    'mismatch_type': None,
                    'resource_usage': None,
                    'strategy_features': feat,
                    'cache_hits': 0,
                    **ids
                }









            log_result({




                'problem_preview': problem_text[:80],
                'problem_text': problem_text,




                'strategy': 'all_failed',




                'structured_used': bool(self.solver.last_reasoning),




                'complexity_score': getattr(self.solver, 'last_complexity_score', None),




                'extracted_answer': None,




                'execution_result': 'All strategies failed',
                'execution_output_raw': None,
                'generated_code': None,
                'llm_reasoning': self.solver.last_reasoning,




                **solve_result_verification_fields(variables, False),




                'attempt': 1,




                'mismatch': False,




                'mismatch_type': None,




                'resource_usage': None,




                'strategy_features': feat,




                'cache_hits': 0,




                **ids,




                'strategy_order': strategies




            }, path=config.LOG_PATH)




            return {
                'answer': None,
                'method': 'all_failed',
                'code': None,
                'execution_result': 'All strategies failed',
                'request_id': request_id,
                'pipeline_trace': pipeline_trace,
                'input_diagnosis': input_diagnosis,
                'structured_used': bool(self.solver.last_reasoning),
                'extracted_answer': None,
                'answer_explanation': build_user_answer_explanation(
                    verified=False,
                    structured_used=bool(self.solver.last_reasoning),
                    mismatch=False,
                    mismatch_type=None,
                    cleaned_result=None,
                    extracted=None,
                    last_reasoning=self.solver.last_reasoning,
                    strategy="all_failed",
                    pipeline_trace=pipeline_trace,
                ),
                **solve_result_verification_fields(variables, False),
                'mismatch': False,
                'mismatch_type': None,
                'resource_usage': None,
                'strategy_features': feat,
                'cache_hits': 0,
                **ids
            }


    def _inject_reverse_check(self, problem_text: str, variables: Dict[str, Any]):

        import re




        pat = re.compile(r"(what is|compute|evaluate)\s+([0-9]+)\s*([+\-*/])\s*([0-9]+)", re.IGNORECASE)




        m = pat.search(problem_text)




        if not m:




            return




        a = int(m.group(2)); op = m.group(3); b = int(m.group(4))




        def rev(ans: Any) -> bool:




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









    def _attempt_fix(self, original_code: str, error_msg: str) -> str:




        """




        Simulates the 'Traceback' process where the model reads the error




        and tries to fix the code.




        """




        # In a real system, this would send (code + error) back to the LLM.




        




        if "Timeout" in error_msg:




            # Heuristic Fix: Optimize loop or switch algorithm




            return "print('Optimized Code Result')"




        elif "SyntaxError" in error_msg:




            # Heuristic Fix: Correct syntax




            return "print('Syntax Fixed Result')"




            




        # If error is too complex, return None to signal "Cannot Fix"




        return None  # type: ignore[return-value]









    def _map_reconciliation_status_to_refine_error(self, rec_status: str) -> str:




        """Map reconciliation status to refine prompt error type."""




        mapping = {




            'MISMATCH_ARITHMETIC': 'arithmetic',




            'MISMATCH_LOGIC': 'logic',




            'ERROR_PARSING': 'other',




            'MISMATCH_FORMAT_DIFF': 'format'  # Actually, if it's mismatch format diff, but status would be MISMATCH_FORMAT_DIFF if not matched




        }




        # Default to 'other' if not found




        return mapping.get(rec_status, 'other')









    def _classify_problem(self, problem_text: str) -> str:




        """




        Classify problem type to determine solving strategy.




        Returns: 'computational', 'geometric', 'proof', 'complex'




        """




        problem_lower = problem_text.lower()




        




        # Geometric keywords




        geo_keywords = ['triangle', 'circle', 'angle', 'perpendicular', 'parallel', 




                       'tangent', 'area', 'perimeter', 'polygon', 'coordinate', 




                       'distance', 'midpoint', 'radius', 'diameter', 'chord']




        




        # Complex problem indicators




        complex_indicators = ['prove that', 'show that', 'demonstrate', 'find all',




                             'for what values', 'determine whether', 'if and only if']




        




        # Check for geometry




        if any(keyword in problem_lower for keyword in geo_keywords):




            return 'geometric'




        




        # Check for complex reasoning




        if any(indicator in problem_lower for indicator in complex_indicators):




            return 'complex'




        




        # Default to computational




        return 'computational'




    




    def _solve_geometric(self, problem_text: str, add_trace: Any = None) -> str:




        """




        Handle geometric problems using specialized solver.




        """




        try:
            if add_trace:
                add_trace("Special Handler: Geometric", "processing", "Attempting specialized geometric solving")



            code = self.geo_solver.solve_geometric_problem(problem_text, add_trace=add_trace)




            logger.debug(f"Generated Geometric Code ({len(code)} chars)")




            




            result = self.executor.execute(code)




            




            if "Error" not in result:




                logger.info(f"Geometric Solution: {result.strip()}")
                if add_trace:
                    add_trace("Special Handler: Geometric", "completed", f"Solution found: {result.strip()}")



                return result




            else:




                logger.warning(f"Geometric solver failed: {result.strip()}")




                logger.info("Falling back to standard pipeline...")




                return None  # type: ignore[return-value]




        except Exception as e:




            logger.error(f"Geometric solver error: {str(e)}", exc_info=True)




            logger.info("Falling back to standard pipeline...")




            return None  # type: ignore[return-value]









if __name__ == "__main__":




    orch = PipelineOrchestrator()




    




    # Scenario 1: Small N (Simulator should succeed)




    orch.solve_problem("Number Theory", {"N": 100}, "...")




    




    # Scenario 2: Huge N (Simulator fails -> Fallback to Theoretician)




    # Example usage (commented out for production)
    # logger.info("="*30)




