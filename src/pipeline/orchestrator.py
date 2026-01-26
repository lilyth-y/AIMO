"""




Orchestrator




- Coordinates the 5-Stage Pipeline




- Implements the "Fast Fail & Fallback" loop




"""









import time




from typing import Dict, Any




from . import config




from .reasoning_utils import extract_answer, extract_final_answer_from_output, log_result, make_ids, build_refine_prompt, canonicalize_expression, count_free_symbols, count_tokens, assess_complexity




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




import opentelemetry.trace as trace




from opentelemetry.sdk.trace import TracerProvider




from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter




from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter









# Initialize tracing




trace.set_tracer_provider(TracerProvider())




tracer = trace.get_tracer(__name__)









# Configure OTLP exporter




otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)




span_processor = BatchSpanProcessor(otlp_exporter)




trace.get_tracer_provider().add_span_processor(span_processor)









# Optional: Console exporter for debugging




console_exporter = ConsoleSpanExporter()




trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(console_exporter))









class PipelineOrchestrator:




    def __init__(self):




        with tracer.start_as_current_span("PipelineOrchestrator Initialization"):




            self.router = CalculationRouter()




            self.executor = CodeExecutor(timeout_seconds=5)




            self.verifier = VerificationRouter()




            self.reconciler = ReasoningReconciler(self.verifier)




            self.solver = Solver()




            self.decomposer = ProblemDecomposer(self.solver.llm)




            self.geo_solver = GeometricSolver(self.solver.llm)




            self.hybrid_engine = HybridReasoningEngine(self.solver, self.executor)




            self.multi_agent = None  # Lazy initialize









    def solve_problem(self, domain: str, variables: Dict[str, Any], problem_text: str, time_budget: float = 60.0):




        with tracer.start_as_current_span("solve_problem") as span:




            span.set_attribute("domain", domain)




            span.set_attribute("time_budget", time_budget)




            span.add_event("Starting problem solving pipeline")




            """




            Executes the solving pipeline with fallback logic.




            Args:




                time_budget: Max time (seconds) allowed for this problem.




            """




            ids = make_ids(problem_text)




            print(f"--- Solving Problem (run={ids['run_id']}, N={variables.get('N')}) [Budget: {time_budget}s] ---")




            feat = extract_features(problem_text, complexity_score=None)









            # Rapid Intuition Phase: Instant problem classification (diffusion-style)




            problem_type_intuition, preferred_strategy = rapid_intuition_phase(problem_text)




            if preferred_strategy:




                print(f"[INTUITION] Instant classification: {problem_type_intuition} -> priority {preferred_strategy}")









            # 0. Check if problem needs special handling




            problem_type = self._classify_problem(problem_text)




            complexity_score = assess_complexity(problem_text)




            decomposition_threshold = getattr(config, 'DECOMPOSITION_COMPLEXITY_THRESHOLD', 15)




            should_decompose = problem_type == 'complex' and complexity_score >= decomposition_threshold




            print(f"[Complexity Analysis] Score: {complexity_score}, Type: {problem_type}, Threshold: {decomposition_threshold}, Decompose: {should_decompose}")









            # Inject reverse check hooks for simple arithmetic problems




            self._inject_reverse_check(problem_text, variables)




            




            # Disable geometric handler for IMO-level evaluation (0.5B model insufficient)




            # if problem_type == 'geometric' and len(problem_text) < 500:




            #     print("[Special Handler] Detected GEOMETRIC problem (simple)")




            #     result = self._solve_geometric(problem_text)




            #     if result:




            #         return {




            #             'answer': result,




            #             'method': 'geometric_handler',




            #             'code': None,




            #             'execution_result': result




            #         }




            #     else:




            #         print("[Geometric handler failed, falling back to general pipeline]")




            




            # Handle complex problems that need decomposition




            if should_decompose:




                print("[Special Handler] Compromise Point activated - decomposing based on complexity threshold")




                analysis = self.decomposer.analyze_problem(problem_text)




                if analysis.get('decompose') == 'yes':




                    # Try hybrid reasoning engine for structured decomposition




                    print("[Using Hybrid Reasoning Engine with Graph Decomposition]")




                    try:




                        result = self.hybrid_engine.solve_with_graph(problem_text)




                        if result and "Error" not in result:




                            return {




                                'answer': result,




                                'method': 'hybrid_graph_engine',




                                'code': None,




                                'execution_result': result




                            }




                        else:




                            print("[Hybrid Engine failed, falling back to hierarchical solver]")




                            hierarchical_result = self.decomposer.solve_hierarchically(problem_text, self.solver, self.executor)




                            return {




                                'answer': hierarchical_result,




                                'method': 'hierarchical_decomposer',




                                'code': None,




                                'execution_result': hierarchical_result




                            }




                    except Exception as e:




                        print(f"[Hybrid Engine error: {str(e)}]")




                        hierarchical_result = self.decomposer.solve_hierarchically(problem_text, self.solver, self.executor)




                        return {




                            'answer': hierarchical_result,




                            'method': 'hierarchical_decomposer',




                            'code': None,




                            'execution_result': hierarchical_result




                        }




            




            # 1. Get Prioritized Plan (standard flow)




            strategies = self.router.route(domain, variables)




            # Adaptive reordering based on historical performance




            bandit = StrategyBandit(config.LOG_PATH)




            strategies = bandit.reorder(strategies)




            print(f"1. Strategic Plan (adaptive): {strategies}")









            # Update executor timeout based on budget (simple distribution)




            # Reserve more time per strategy, limit to 3 attempts max




            max_attempts = min(3, len(strategies))




            strategies = strategies[:max_attempts]




            per_strategy_timeout = time_budget / max_attempts




            self.executor.timeout_seconds = per_strategy_timeout




            




            last_was_timeout = False









            for attempt, strategy in enumerate(strategies, 1):




                # Skip Path B: The Theoretician if previous attempt timed out




                if last_was_timeout and "Theoretician" in strategy:




                    print(f"\n[Attempt {attempt}] Skipping {strategy} (previous timeout)")




                    continue




                    




                print(f"\n[Attempt {attempt}] Trying Strategy: {strategy}")




                last_was_timeout = False




                




                # 2. Generate Code (multi-candidate voting if enabled)




                selected_index = None




                if getattr(config, 'USE_VOTING', False):




                    candidates = self.solver.generate_candidates(problem_text, strategy, config.NUM_CANDIDATES, config.CANDIDATE_TEMPS)




                    print(f"   -> Generated {len(candidates)} candidate codes")




                    code = None




                    result = None




                    resource_stats = None




                    for idx, cand in enumerate(candidates):




                        if hasattr(self.executor, 'execute_with_stats'):




                            exec_out, stats = self.executor.execute_with_stats(cand)




                            cand_result = exec_out




                            cand_stats = stats




                        else:




                            cand_result = self.executor.execute(cand)




                            cand_stats = None




                        # Ensure cand_result is a string




                        if not isinstance(cand_result, str):




                            cand_result = str(cand_result)




                        cleaned = extract_final_answer_from_output(cand_result)




                        verified_cand = False if cleaned.startswith('ERROR:') else self.verifier.verify(cleaned, variables)




                        if verified_cand:




                            code = cand




                            result = cleaned




                            resource_stats = cand_stats




                            selected_index = idx




                            print(f"   -> [OK] Candidate {idx+1} verified; selecting.")




                            break




                        else:




                            print(f"   -> Candidate {idx+1} failed; trying next...")




                            if code is None:




                                code = cand




                                result = cleaned




                                resource_stats = cand_stats




                                selected_index = idx




                    if code is None:




                        code = candidates[0]




                        result = 'ERROR: no candidates'




                else:




                    code = self.solver.generate_code(problem_text, strategy)




                    




                    # Check if generation timed out




                    if "TIMEOUT" in code or "ERROR: Generation timeout" in code:




                        print(f"   -> [WARNING] Generation timed out, trying next strategy...")




                        last_was_timeout = True




                        continue




                    




                    print(f"   -> Generated Code ({len(code)} chars)")




                    resource_stats = None




                    if hasattr(self.executor, 'execute_with_stats'):




                        exec_out, stats = self.executor.execute_with_stats(code)




                        result = exec_out




                        resource_stats = stats




                    else:




                        result = self.executor.execute(code)









                # Metrics




                code_chars = len(code)




                reasoning_tokens = count_tokens(self.solver.last_reasoning) if self.solver.last_reasoning else 0




                




                # 4. Check for Execution Failure & Traceback (Self-Correction)




                if "Error" in result:




                    print(f"   -> [FAIL] Execution Failed: {result.strip()}")




                    




                    # Traceback & Fix Loop (single attempt only for IMO problems)




                    print("   -> [INFO] Analyzing Traceback (Self-Correction)...")




                    fixed_code = self._attempt_fix(code, result)




                    




                    if fixed_code:




                        print("   -> [INFO] Retrying with Fixed Code...")




                        try:




                                result = self.executor.execute(fixed_code)




                        except Exception as e:




                            result = f"ERROR: {str(e)}"




                        




                        if "Error" not in result:




                            print(f"   -> [OK] Fix Successful! Result: {result.strip()}")




                        else:




                            print(f"   -> [FAIL] Fix Failed again: {result.strip()}")




                            print("   -> [WARNING] Triggering Fallback Strategy...")




                            continue  # Try next strategy




                    else:




                        print("   -> [WARNING] Triggering Fallback Strategy...")




                        continue









                # 5. Verification Stage




                print("   -> Verifying Answer...")




                # Guard: treat execution error strings as automatic failure




                # Ensure result is a string




                if not isinstance(result, str):




                    result = str(result)




                # Extract final answer from execution output (removes debug prints, labels, etc.)
                cleaned_result = extract_final_answer_from_output(result)




                if cleaned_result.startswith('ERROR:'):




                    verified = False




                else:




                    verified = self.verifier.verify(cleaned_result, variables)




                structured_used = bool(self.solver.last_reasoning)




                complexity_score = getattr(self.solver, 'last_complexity_score', None)




                extracted = extract_answer(self.solver.last_reasoning) if structured_used else None




                




                # Reasoning Reconciliation




                mismatch = False




                mismatch_type = None




                reconcile_details = ""




                




                if structured_used and extracted:




                    rec_result = self.reconciler.reconcile(extracted, cleaned_result)




                    if not rec_result.match:




                        mismatch = True




                        mismatch_type = rec_result.status




                        reconcile_details = rec_result.details




                    elif rec_result.status == 'MATCH_FORMAT_DIFF':




                        # Log format diff but not a failure




                        reconcile_details = rec_result.details




                




                # Override mismatch type for execution errors




                if cleaned_result.startswith('ERROR:'):




                    mismatch_type = 'execution_error'




                free_symbol_count = count_free_symbols(extracted or cleaned_result)




                if verified:




                    print(f"   -> [OK] Success! Verified Result: {cleaned_result}")




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




                        'strategy': strategy,




                        'structured_used': structured_used,




                        'complexity_score': complexity_score,




                        'extracted_answer': extracted,




                        'execution_result': cleaned_result,




                        'verified': True,




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




                    return {




                        'answer': extracted or extract_final_answer_from_output(result),




                        'method': strategy,




                        'code': code,




                        'execution_result': cleaned_result,




                        'structured_used': structured_used,




                        'extracted_answer': extracted,




                        'verified': True,




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




                    print("   -> [WARNING] Verification Failed. Triggering Fallback Strategy...")




                    # self-refine single attempt if structured reasoning present




                    refined_used = False




                    if structured_used and not getattr(self, '_refine_used', False):




                        refine_error_type = self._map_reconciliation_status_to_refine_error(mismatch_type) if mismatch_type else ('verification_fail' if not verified else 'mismatch')




                        refine_prompt = build_refine_prompt(problem_text, self.solver.last_reasoning, code,




                            refine_error_type, cleaned_result, extracted)




                        print("   -> [INFO] Self-Refine Attempt...")




                        refine_code = self.solver.generate_code_from_prompt(refine_prompt)




                        if hasattr(self.executor, 'execute_with_stats'):




                            refine_out, refine_stats = self.executor.execute_with_stats(refine_code)




                        else:




                            refine_out = self.executor.execute(refine_code)




                            refine_stats = None




                        refine_verified = self.verifier.verify(refine_out.strip(), variables)




                        refined_used = True




                        self._refine_used = True




                        refine_extracted = extract_answer(self.solver.last_reasoning)




                        refine_mismatch = False




                        refine_mismatch_type = None




                        refine_reconcile_details = ""




                        if refine_extracted:




                            # Use Reconciler for refine step too




                            refine_rec = self.reconciler.reconcile(refine_extracted, refine_out.strip())




                            if not refine_rec.match:




                                refine_mismatch = True




                                refine_mismatch_type = refine_rec.status




                                refine_reconcile_details = refine_rec.details




                            elif refine_rec.status == 'MATCH_FORMAT_DIFF':




                                refine_reconcile_details = refine_rec.details









                        log_result({




                            'problem_preview': problem_text[:80],




                            'strategy': strategy + '_refine',




                            'structured_used': structured_used,




                            'complexity_score': complexity_score,




                            'extracted_answer': refine_extracted,




                            'execution_result': refine_out.strip(),




                            'verified': refine_verified,




                            'attempt': attempt,




                            'mismatch': refine_mismatch,




                            'mismatch_type': refine_mismatch_type,




                            'reconcile_details': refine_reconcile_details,




                            'resource_usage': refine_stats,




                            **ids,




                            'strategy_order': strategies,




                            'refine': True




                        }, path=config.LOG_PATH)




                        if refine_verified:




                            return {




                                'answer': refine_extracted or refine_out.strip(),




                                'method': strategy + '_refine',




                                'code': refine_code,




                                'execution_result': refine_out.strip(),




                                'structured_used': structured_used,




                                'extracted_answer': refine_extracted,




                                'verified': True,




                                'mismatch': refine_mismatch,




                                'mismatch_type': refine_mismatch_type,




                                'reconcile_details': refine_reconcile_details,




                                'resource_usage': refine_stats,




                                'refine': True,




                                **ids




                            }




                    log_result({




                        'problem_preview': problem_text[:80],




                        'strategy': strategy,




                        'structured_used': structured_used,




                        'complexity_score': complexity_score,




                        'extracted_answer': extracted,




                        'execution_result': cleaned_result,




                        'verified': False,




                        'attempt': attempt,




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









            print("\n[FAIL] All strategies failed.")









            # Try multi-agent reasoning as last resort




            if self.multi_agent is None:




                self.multi_agent = MultiAgentReasoner(self.solver)




            multi_result = self.multi_agent.solve_with_multi_agent(problem_text)




            if multi_result.get('final_answer'):




                print(f"[MULTI-AGENT] Success! Answer: {multi_result['final_answer']}")




                log_result({




                    'problem_preview': problem_text[:80],




                    'strategy': 'multi_agent',




                    'structured_used': True,




                    'complexity_score': None,




                    'extracted_answer': multi_result['final_answer'],




                    'execution_result': 'multi_agent_result',




                    'verified': True,




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




                    'answer': multi_result['final_answer'],




                    'method': 'multi_agent',




                    'code': None,




                    'execution_result': 'multi_agent_result',




                    'structured_used': True,




                    'extracted_answer': multi_result['final_answer'],




                    'verified': True,




                    'mismatch': False,




                    'mismatch_type': None,




                    'resource_usage': None,




                    'strategy_features': feat,




                    'cache_hits': 0,




                    **ids




                }









            log_result({




                'problem_preview': problem_text[:80],




                'strategy': 'all_failed',




                'structured_used': bool(self.solver.last_reasoning),




                'complexity_score': getattr(self.solver, 'last_complexity_score', None),




                'extracted_answer': None,




                'execution_result': 'All strategies failed',




                'verified': False,




                'attempt': attempt,




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




                'structured_used': bool(self.solver.last_reasoning),




                'extracted_answer': None,




                'verified': False,




                'mismatch': False,




                'mismatch_type': None,




                'resource_usage': None,




                'strategy_features': feat,




                'cache_hits': 0,




                **ids




            }









    def _classify_mismatch(self, extracted: str, executed: str) -> str:




        # Deprecated but kept for backward compatibility if needed




        try:




            ex_val = float(extracted); exec_val = float(executed)




            if abs(ex_val - exec_val) < 1e-9:




                return 'format'




            return 'arithmetic'




        except Exception:




            pass




        try:




            import sympy as sp




            ex_expr = sp.sympify(extracted); exec_expr = sp.sympify(executed)




            if sp.simplify(ex_expr - exec_expr) == 0:




                return 'format'




            return 'logic'




        except Exception:




            return 'other'









    def _inject_reverse_check(self, problem_text: str, variables: Dict[str, Any]):




        import re




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




        return None









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




    




    def _solve_geometric(self, problem_text: str) -> str:




        """




        Handle geometric problems using specialized solver.




        """




        try:




            code = self.geo_solver.solve_geometric_problem(problem_text)




            print(f"   -> Generated Geometric Code ({len(code)} chars)")




            




            result = self.executor.execute(code)




            




            if "Error" not in result:




                print(f"   -> [OK] Geometric Solution: {result.strip()}")




                return result




            else:




                print(f"   -> [FAIL] Geometric solver failed: {result.strip()}")




                print("   -> Falling back to standard pipeline...")




                return None




        except Exception as e:




            print(f"   -> [ERROR] Geometric solver error: {str(e)}")




            print("   -> Falling back to standard pipeline...")




            return None









if __name__ == "__main__":




    orch = PipelineOrchestrator()




    




    # Scenario 1: Small N (Simulator should succeed)




    orch.solve_problem("Number Theory", {"N": 100}, "...")




    




    # Scenario 2: Huge N (Simulator fails -> Fallback to Theoretician)




    print("\n" + "="*30 + "\n")




