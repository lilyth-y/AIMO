"""
Self-Refine Loop 모듈
검증 실패 시 자동으로 코드를 개선하는 루프 시스템
"""

from typing import Dict, Any, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .solver import Solver
    from .stage4_execution import CodeExecutor
    from .stage5_verification import VerificationRouter
    from .reconciliation import ReasoningReconciler

from .reasoning_utils import build_refine_prompt, extract_answer
from .orchestrator_helpers import map_reconciliation_status_to_refine_error
from .logger import get_logger

logger = get_logger()


class RefineLoop:
    """
    Self-Refine Loop 클래스
    검증 실패 시 여러 번 시도하여 코드를 개선합니다.
    """
    
    def __init__(self, max_iterations: int = 3, enable_loop: bool = True):
        """
        Args:
            max_iterations: 최대 반복 횟수
            enable_loop: 루프 활성화 여부
        """
        self.max_iterations = max_iterations
        self.enable_loop = enable_loop
        self.iteration_count = 0
    
    def should_refine(self, 
                     structured_used: bool,
                     verified: bool,
                     refine_used: bool = False) -> bool:
        """
        Refine을 시도해야 하는지 판단합니다.
        
        Args:
            structured_used: Structured reasoning이 사용되었는지
            verified: 검증이 통과했는지
            refine_used: 이미 refine을 사용했는지
        
        Returns:
            refine을 시도해야 하면 True
        """
        if not self.enable_loop:
            return False
        
        if verified:
            return False
        
        if not structured_used:
            return False
        
        if refine_used and self.iteration_count >= self.max_iterations:
            return False
        
        return True
    
    def refine_attempt(self,
                      solver: "Solver",
                      executor: "CodeExecutor",
                      verifier: "VerificationRouter",
                      reconciler: "ReasoningReconciler",
                      problem_text: str,
                      previous_reasoning: Optional[str],
                      previous_code: str,
                      execution_result: str,
                      extracted_answer: Optional[str],
                      mismatch_type: Optional[str],
                      variables: Dict[str, Any],
                      strategy: str) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        한 번의 refine 시도를 수행합니다.
        
        Args:
            solver: Solver 인스턴스
            executor: CodeExecutor 인스턴스
            verifier: VerificationRouter 인스턴스
            reconciler: ReasoningReconciler 인스턴스
            problem_text: 문제 텍스트
            previous_reasoning: 이전 추론 텍스트
            previous_code: 이전 코드
            execution_result: 실행 결과
            extracted_answer: 추출된 답
            mismatch_type: 불일치 타입
            variables: 변수 딕셔너리
            strategy: 현재 전략
        
        Returns:
            (결과 딕셔너리 또는 None, 성공 여부)
        """
        self.iteration_count += 1
        
        # 에러 타입 결정
        refine_error_type = (
            map_reconciliation_status_to_refine_error(mismatch_type) 
            if mismatch_type 
            else 'verification_fail'
        )
        
        # Refine 프롬프트 생성
        refine_prompt = build_refine_prompt(
            problem_text,
            previous_reasoning,
            previous_code,
            refine_error_type,
            execution_result,
            extracted_answer
        )
        
        logger.info(f"Self-Refine Attempt {self.iteration_count}/{self.max_iterations}...")
        logger.info(f"Error Type: {refine_error_type}")
        
        # 코드 생성
        refine_code = solver.generate_code_from_prompt(refine_prompt)
        
        # 코드 실행
        if hasattr(executor, 'execute_with_stats'):
            refine_out, refine_stats = executor.execute_with_stats(refine_code)
        else:
            refine_out = executor.execute(refine_code)
            refine_stats = None
        
        # 결과 정리
        if not isinstance(refine_out, str):
            refine_out = str(refine_out)
        
        refine_cleaned = refine_out.strip()
        
        # 검증
        refine_verified = verifier.verify(refine_cleaned, variables)
        
        # Reconciliation
        refine_extracted = extract_answer(solver.last_reasoning) if solver.last_reasoning else None
        refine_mismatch = False
        refine_mismatch_type = None
        refine_reconcile_details = ""
        
        if refine_extracted:
            refine_rec = reconciler.reconcile(refine_extracted, refine_cleaned)
            if not refine_rec.match:
                refine_mismatch = True
                refine_mismatch_type = refine_rec.status
                refine_reconcile_details = refine_rec.details
            elif refine_rec.status == 'MATCH_FORMAT_DIFF':
                refine_reconcile_details = refine_rec.details
        
        # 성공한 경우
        if refine_verified:
            logger.info(f"Refine Success! Result: {refine_cleaned}")
            return {
                'answer': refine_extracted or refine_cleaned,
                'method': f"{strategy}_refine_{self.iteration_count}",
                'code': refine_code,
                'execution_result': refine_cleaned,
                'structured_used': bool(previous_reasoning),
                'extracted_answer': refine_extracted,
                'verified': True,
                'mismatch': refine_mismatch,
                'mismatch_type': refine_mismatch_type,
                'reconcile_details': refine_reconcile_details,
                'resource_usage': refine_stats,
                'refine': True,
                'refine_iteration': self.iteration_count
            }, True
        
        # 실패한 경우
        logger.warning(f"Refine Attempt {self.iteration_count} Failed")
        return None, False
    
    def reset(self):
        """루프 상태를 초기화합니다."""
        self.iteration_count = 0
    
    def can_continue(self) -> bool:
        """계속 refine을 시도할 수 있는지 확인합니다."""
        return self.iteration_count < self.max_iterations


def create_refine_loop(max_iterations: int = 3, enable_loop: bool = True) -> RefineLoop:
    """
    RefineLoop 인스턴스를 생성하는 팩토리 함수입니다.
    
    Args:
        max_iterations: 최대 반복 횟수
        enable_loop: 루프 활성화 여부
    
    Returns:
        RefineLoop 인스턴스
    """
    """
    RefineLoop 인스턴스를 생성합니다.
    
    Args:
        max_iterations: 최대 반복 횟수
        enable_loop: 루프 활성화 여부
    
    Returns:
        RefineLoop 인스턴스
    """
    return RefineLoop(max_iterations=max_iterations, enable_loop=enable_loop)
