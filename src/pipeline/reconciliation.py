"""
추론-답변 조정 모듈 (고급 불일치 분류) - P0-2 개선

추출된 답변과 실행 결과를 비교하고 불일치를 정확하게 분류합니다.
SymPy 기반 정규화를 통해 잘못된 불일치를 감소시킵니다.

개선사항:
- ANS 추출 강화 (answer_extraction.py 연동)
- 거짓 불일치 감소
- 상세 분류 정확도 향상
"""

from typing import Any, Optional, Dict
from dataclasses import dataclass
from .stage5_verification import VerificationRouter
from .answer_extraction import extract_answer_from_reasoning
from .logger import get_logger

logger = get_logger()

try:
    import sympy as sp
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False
    sp = None


@dataclass
class ReconciliationResult:
    """
    조정 결과
    
    Attributes:
        match: 두 값이 일치하는지 여부
        status: 조정 상태 (MATCH_EXACT, MATCH_FORMAT_DIFF, MISMATCH_ARITHMETIC, MISMATCH_LOGIC, ERROR_PARSING, ERROR_MISSING)
        details: 상세 정보
    """
    match: bool
    status: str  # 'MATCH_EXACT', 'MATCH_FORMAT_DIFF', 'MISMATCH_ARITHMETIC', 'MISMATCH_LOGIC', 'ERROR_PARSING', 'ERROR_MISSING'
    details: str = ""


class ReasoningReconciler:
    """
    추론-답변 조정기
    
    추출된 답변과 실행 결과를 비교하고 불일치를 정확하게 분류합니다.
    SymPy 기반 정규화를 통해 잘못된 불일치를 감소시킵니다.
    """
    
    def __init__(self, verifier: Optional[VerificationRouter] = None):
        """
        Args:
            verifier: 검증 라우터 (None이면 새로 생성)
        """
        self.verifier = verifier if verifier else VerificationRouter()

    def reconcile(self, extracted_answer: Any, execution_result: Any) -> ReconciliationResult:
        """
        추출된 답변과 실행 결과를 조정합니다.
        
        Args:
            extracted_answer: 추론 텍스트에서 추출된 답변 (예: <ANS>)
            execution_result: 코드 실행 결과
        
        Returns:
            ReconciliationResult: 조정 결과
        """
        if extracted_answer is None or execution_result is None:
            logger.debug("Reconciliation failed: One of the answers is None")
            return ReconciliationResult(False, 'ERROR_MISSING', "One of the answers is None")

        # 1. Parse both to comparable forms
        parsed_ex = self.verifier._parse_answer(extracted_answer)
        parsed_exec = self.verifier._parse_answer(execution_result)

        if parsed_ex is None or parsed_exec is None:
            logger.debug(f"Reconciliation failed: Cannot parse - Ex='{extracted_answer}', Exec='{execution_result}'")
            return ReconciliationResult(False, 'ERROR_PARSING', 
                                       f"Cannot parse: Ex='{extracted_answer}', Exec='{execution_result}'")

        # 2. Enhanced comparison with SymPy normalization
        if self._compare_with_normalization(parsed_ex, parsed_exec):
            # If they compare equal, check if string representation is different (Format Mismatch)
            if str(extracted_answer).strip() != str(execution_result).strip():
                logger.debug(f"Format mismatch: '{extracted_answer}' vs '{execution_result}' (values match)")
                return ReconciliationResult(True, 'MATCH_FORMAT_DIFF', 
                                          f"Values match but formats differ: '{extracted_answer}' vs '{execution_result}'")
            logger.debug("Exact match")
            return ReconciliationResult(True, 'MATCH_EXACT', "Exact match")

        # 3. Enhanced mismatch classification
        mismatch_type, details = self._classify_mismatch(parsed_ex, parsed_exec, extracted_answer, execution_result)
        logger.debug(f"Mismatch detected: {mismatch_type} - {details}")
        return ReconciliationResult(False, mismatch_type, details)
    
    def _compare_with_normalization(self, a: Any, b: Any) -> bool:
        """
        정규화 후 비교 (SymPy 기반).
        
        Args:
            a: 첫 번째 값
            b: 두 번째 값
        
        Returns:
            두 값이 동등한지 여부
        """
        # VerificationRouter의 고급 비교 사용
        return self.verifier._compare(a, b)
    
    def _classify_mismatch(
        self, 
        parsed_ex: Any, 
        parsed_exec: Any, 
        extracted_answer: Any, 
        execution_result: Any
    ) -> tuple[str, str]:
        """
        불일치를 분류합니다.
        
        Args:
            parsed_ex: 파싱된 추출 답변
            parsed_exec: 파싱된 실행 결과
            extracted_answer: 원본 추출 답변
            execution_result: 원본 실행 결과
        
        Returns:
            (불일치 타입, 상세 정보)
        """
        # 1. 숫자 불일치 (산술 오류)
        is_num_ex = isinstance(parsed_ex, (int, float))
        is_num_exec = isinstance(parsed_exec, (int, float))
        
        if is_num_ex and is_num_exec:
            diff = abs(float(parsed_ex) - float(parsed_exec))
            relative_diff = diff / max(abs(float(parsed_ex)), abs(float(parsed_exec)), 1e-10)
            
            # 매우 작은 차이는 부동소수점 오차일 수 있음
            if diff < 1e-9 or relative_diff < 1e-9:
                return 'MATCH_FORMAT_DIFF', f"Very small numeric difference (likely floating point error): {diff}"
            
            return 'MISMATCH_ARITHMETIC', f"Numeric difference: {parsed_ex} vs {parsed_exec} (diff: {diff}, relative: {relative_diff:.2e})"
        
        # 2. SymPy 표현식 불일치 (로직 오류)
        if SYMPY_AVAILABLE:
            try:
                sym_ex = sp.sympify(parsed_ex) if not isinstance(parsed_ex, sp.Basic) else parsed_ex
                sym_exec = sp.sympify(parsed_exec) if not isinstance(parsed_exec, sp.Basic) else parsed_exec
                
                # 정규화 후 비교
                diff = sp.simplify(sym_ex - sym_exec)
                
                # 0이 아니면 로직 불일치
                if diff != 0:
                    # 더 자세한 정보 제공
                    try:
                        diff_str = str(diff)
                        if len(diff_str) > 100:
                            diff_str = diff_str[:100] + "..."
                        return 'MISMATCH_LOGIC', f"Symbolic difference: {diff_str}"
                    except Exception:
                        return 'MISMATCH_LOGIC', f"Symbolic expressions differ: {parsed_ex} vs {parsed_exec}"
            except Exception as e:
                logger.debug(f"SymPy comparison failed: {e}")
        
        # 3. 리스트/집합 불일치
        if isinstance(parsed_ex, (list, tuple)) and isinstance(parsed_exec, (list, tuple)):
            if len(parsed_ex) != len(parsed_exec):
                return 'MISMATCH_LOGIC', f"List length mismatch: {len(parsed_ex)} vs {len(parsed_exec)}"
            return 'MISMATCH_LOGIC', f"List content mismatch: {parsed_ex} vs {parsed_exec}"
        
        if isinstance(parsed_ex, set) and isinstance(parsed_exec, set):
            if len(parsed_ex) != len(parsed_exec):
                return 'MISMATCH_LOGIC', f"Set size mismatch: {len(parsed_ex)} vs {len(parsed_exec)}"
            return 'MISMATCH_LOGIC', f"Set content mismatch: {parsed_ex} vs {parsed_exec}"
        
        # 4. 일반 불일치
        return 'MISMATCH_LOGIC', f"Structural/Logic mismatch: {parsed_ex} vs {parsed_exec}"
