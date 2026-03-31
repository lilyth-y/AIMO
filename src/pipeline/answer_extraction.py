"""
ANS 추출 강화 모듈 (P0-2 작업)

목표:
- LaTeX 형식 지원
- 다중 형식 처리
- 오류 처리 및 로깅

위치: src/pipeline/answer_extraction.py
"""

import re
from typing import Any, Optional, TYPE_CHECKING
from dataclasses import dataclass

from .logger import get_logger

logger = get_logger()

# SymPy availability flag
_sympy_available = False

if TYPE_CHECKING:
    import sympy as sp
else:
    try:
        import sympy as sp
        _sympy_available = True
    except ImportError:
        sp = None  # type: ignore
        _sympy_available = False

def is_sympy_available() -> bool:
    """Check if SymPy is available."""
    return _sympy_available


@dataclass
class ExtractionResult:
    """
    추출 결과
    
    Attributes:
        value: 추출된 값
        format: 추출된 형식 (INT, FLOAT, LATEX, EXPRESSION, LIST, etc.)
        original_text: 원본 텍스트
        confidence: 추출 신뢰도 (0.0-1.0)
        error: 에러 메시지
    """
    value: Any
    format: str
    original_text: str
    confidence: float = 1.0
    error: Optional[str] = None


class AnswerExtractor:
    """ANS 태그 및 다양한 형식의 답변을 추출합니다."""
    
    def __init__(self):
        """초기화"""
        # *? : 빈 <ANS></ANS> 도 잡아 EMPTY 등으로 처리
        self.ans_tag_pattern = r"<ANS>\s*(.*?)\s*</ANS>"
        self.float_pattern = r'^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$'
        self.int_pattern = r'^[-+]?[0-9]+$'
        self.latex_frac_pattern = r'\\frac\{([^}]+)\}\{([^}]+)\}'
        self.list_pattern = r'^\s*\[\s*(.+)\s*\]$'
        self.set_pattern = r'^\s*\{\s*(.+)\s*\}$'
        
        # Unicode symbolic normalization mapping
        self.symbol_map = {
            'π': 'pi',
            'τ': '2*pi',
            '√': 'sqrt',
            '∞': 'oo',
            '≈': '=',
            '≠': '!=',
            '≤': '<=',
            '≥': '>=',
            '±': 'plus_minus',  # Special handling might be needed
            '×': '*',
            '÷': '/',
            '⋅': '*',
            '°': '*pi/180',
            '½': '1/2',
            '⅓': '1/3',
            '⅔': '2/3',
            '¼': '1/4',
            '¾': '3/4',
            '²': '**2',
            '³': '**3',
        }

    def normalize_math_text(self, text: str) -> str:
        """
        유니코드 수학 기호를 표준 ASCII/LaTeX 형식으로 변환합니다.
        
        Args:
            text: 정규화할 텍스트
            
        Returns:
            정규화된 텍스트
        """
        if not text:
            return ""
            
        # 1. 공백 정규화 (Zero-width spaces, Non-breaking spaces 등 제거)
        text = re.sub(r'[\u200b\u200c\u200d\uFEFF\u00A0]', ' ', text)
        
        # 2. 기호 치환
        for unicode_sym, ascii_sym in self.symbol_map.items():
            text = text.replace(unicode_sym, ascii_sym)
            
        # 3. LaTeX 스타일 기호 간소화 (예: \pi -> pi)
        text = text.replace('\\pi', 'pi').replace('\\infty', 'oo')
        
        return text.strip()
    
    def extract_from_text(self, text: str) -> ExtractionResult:
        """
        텍스트에서 <ANS> 태그를 찾아 값을 추출합니다.
        
        Args:
            text: 추론 텍스트
        
        Returns:
            ExtractionResult
        """
        text = text.strip() if text else ""
        
        # 1. <ANS> 태그 찾기
        match = re.search(self.ans_tag_pattern, text, re.DOTALL | re.IGNORECASE)
        if not match:
            return ExtractionResult(
                value=None,
                format="NOT_FOUND",
                original_text=text,
                confidence=0.0,
                error="No <ANS> tag found in text"
            )
        
        ans_text = match.group(1).strip()
        return self._parse_answer_text(ans_text)
    
    def _parse_answer_text(self, ans_text: str) -> ExtractionResult:
        """
        ANS 태그 내용을 파싱합니다.
        
        Args:
            ans_text: <ANS>...</ANS> 사이의 텍스트
        
        Returns:
            ExtractionResult
        """
        original = ans_text
        ans_text = self.normalize_math_text(ans_text)
        
        # 2. 빈 문자열 처리
        if not ans_text:
            return ExtractionResult(
                value=None,
                format="EMPTY",
                original_text=original,
                confidence=0.0,
                error="ANS tag is empty"
            )
        
        # 3. 정수 시도
        if re.match(self.int_pattern, ans_text):
            try:
                val = int(ans_text)
                return ExtractionResult(
                    value=val,
                    format="INT",
                    original_text=original,
                    confidence=1.0
                )
            except ValueError:
                pass
        
        # 4. 부동소수점 시도
        if re.match(self.float_pattern, ans_text):
            try:
                val = float(ans_text)
                return ExtractionResult(
                    value=val,
                    format="FLOAT",
                    original_text=original,
                    confidence=1.0
                )
            except ValueError:
                pass
        
        # 5. LaTeX 분수 시도
        frac_match = re.search(self.latex_frac_pattern, ans_text)
        if frac_match:
            numerator_str = frac_match.group(1).strip()
            denominator_str = frac_match.group(2).strip()
            
            result = self._parse_latex_fraction(
                numerator_str, denominator_str, original
            )
            if result.value is not None:
                return result
        
        # 6. 리스트 시도
        list_match = re.match(self.list_pattern, ans_text)
        if list_match:
            result = self._parse_list(list_match.group(1), original)
            if result.value is not None:
                return result
        
        # 7. 집합 시도
        set_match = re.match(self.set_pattern, ans_text)
        if set_match:
            result = self._parse_set(set_match.group(1), original)
            if result.value is not None:
                return result
        
        # 8. SymPy 표현식 시도
        if is_sympy_available():
            result = self._parse_sympy_expression(ans_text, original)
            if result.value is not None:
                return result
        
        # 9. 일반 문자열로 반환 (신뢰도 낮음)
        return ExtractionResult(
            value=ans_text,
            format="STRING",
            original_text=original,
            confidence=0.5,
            error="Could not parse as specific type; treated as string"
        )
    
    def _parse_latex_fraction(
        self, 
        numerator_str: str, 
        denominator_str: str,
        original: str
    ) -> ExtractionResult:
        """
        LaTeX 분수를 파싱합니다.
        
        Args:
            numerator_str: 분자 텍스트
            denominator_str: 분모 텍스트
            original: 원본 텍스트
        
        Returns:
            ExtractionResult
        """
        try:
            # 분자, 분모를 재귀적으로 파싱
            num_result = self._parse_answer_text(numerator_str)
            den_result = self._parse_answer_text(denominator_str)
            
            if num_result.value is None or den_result.value is None:
                return ExtractionResult(
                    value=None,
                    format="LATEX_FRAC_PARSE_ERROR",
                    original_text=original,
                    confidence=0.3,
                    error=f"Cannot parse fraction numerator or denominator"
                )
            
            num = float(num_result.value) if isinstance(num_result.value, (int, float)) else num_result.value
            den = float(den_result.value) if isinstance(den_result.value, (int, float)) else den_result.value
            
            # 0으로 나누기 체크
            if den == 0:
                return ExtractionResult(
                    value=None,
                    format="LATEX_FRAC_DIV_ZERO",
                    original_text=original,
                    confidence=0.0,
                    error="Division by zero in fraction"
                )
            
            # SymPy로 정규화
            if is_sympy_available():
                try:
                    result = sp.Rational(num) / sp.Rational(den)  # type: ignore[operator]
                    return ExtractionResult(
                        value=result,
                        format="LATEX_FRAC",
                        original_text=original,
                        confidence=1.0
                    )
                except Exception:
                    pass
            
            # 기본 나누기
            val = num / den
            return ExtractionResult(
                value=val,
                format="LATEX_FRAC",
                original_text=original,
                confidence=0.9
            )
        except Exception as e:
            logger.debug(f"LaTeX fraction parsing failed: {e}")
            return ExtractionResult(
                value=None,
                format="LATEX_FRAC_ERROR",
                original_text=original,
                confidence=0.0,
                error=str(e)
            )
    
    def _parse_list(self, list_str: str, original: str) -> ExtractionResult:
        """
        리스트 형식을 파싱합니다.
        
        Args:
            list_str: 리스트 내용 (괄호 제외)
            original: 원본 텍스트
        
        Returns:
            ExtractionResult
        """
        try:
            # 쉼표로 분리
            items = [item.strip() for item in list_str.split(',')]
            
            parsed_items: list = []  # type: ignore[type-arg]
            for item in items:
                # 각 항목을 파싱
                item_result = self._parse_answer_text(item)
                if item_result.value is None:
                    logger.debug(f"Cannot parse list item: {item}")
                    return ExtractionResult(
                        value=None,
                        format="LIST_ITEM_PARSE_ERROR",
                        original_text=original,
                        confidence=0.3,
                        error=f"Cannot parse list item: {item}"
                    )
                parsed_items.append(item_result.value)
            
            return ExtractionResult(
                value=parsed_items,
                format="LIST",
                original_text=original,
                confidence=1.0 if parsed_items else 0.5
            )
        except Exception as e:
            logger.debug(f"List parsing failed: {e}")
            return ExtractionResult(
                value=None,
                format="LIST_ERROR",
                original_text=original,
                confidence=0.0,
                error=str(e)
            )
    
    def _parse_set(self, set_str: str, original: str) -> ExtractionResult:
        """
        집합 형식을 파싱합니다.
        
        Args:
            set_str: 집합 내용 (괄호 제외)
            original: 원본 텍스트
        
        Returns:
            ExtractionResult
        """
        try:
            # 쉼표로 분리
            items = [item.strip() for item in set_str.split(',')]
            
            parsed_items = []
            for item in items:
                item_result = self._parse_answer_text(item)
                if item_result.value is None:
                    logger.debug(f"Cannot parse set item: {item}")
                    return ExtractionResult(
                        value=None,
                        format="SET_ITEM_PARSE_ERROR",
                        original_text=original,
                        confidence=0.3,
                        error=f"Cannot parse set item: {item}"
                    )
                parsed_items.append(item_result.value)
            
            # 집합으로 변환
            try:
                result_set = set(parsed_items)  # type: ignore[arg-type]
            except TypeError:
                # unhashable 타입이면 튜플 리스트로
                result_set = parsed_items  # type: ignore[assignment]
            
            return ExtractionResult(
                value=result_set,
                format="SET",
                original_text=original,
                confidence=1.0 if result_set else 0.5
            )
        except Exception as e:
            logger.debug(f"Set parsing failed: {e}")
            return ExtractionResult(
                value=None,
                format="SET_ERROR",
                original_text=original,
                confidence=0.0,
                error=str(e)
            )
    
    def _parse_sympy_expression(
        self, 
        ans_text: str, 
        original: str
    ) -> ExtractionResult:
        """
        SymPy 표현식을 파싱합니다.
        
        Args:
            ans_text: 파싱할 텍스트
            original: 원본 텍스트
        
        Returns:
            ExtractionResult
        """
        if not is_sympy_available():
            return ExtractionResult(
                value=None,
                format="SYMPY_NOT_AVAILABLE",
                original_text=original,
                confidence=0.0
            )
        
        try:
            # 위험한 문자열 필터링
            dangerous_patterns = ['__', 'exec', 'eval', 'import', 'open']
            if any(p in ans_text for p in dangerous_patterns):
                return ExtractionResult(
                    value=None,
                    format="SYMPY_DANGEROUS",
                    original_text=original,
                    confidence=0.0,
                    error="Dangerous pattern detected"
                )
            
            # SymPy로 파싱
            # implicit multiplication 허용 (예: 2x -> 2*x)
            from sympy.parsing.sympy_parser import (
                parse_expr, standard_transformations, 
                implicit_multiplication_application
            )
            transformations = (standard_transformations + (implicit_multiplication_application,))
            
            # Use parse_expr for more robust parsing than sympify
            expr = parse_expr(ans_text, transformations=transformations)
            
            return ExtractionResult(
                value=expr,
                format="SYMPY_EXPR",
                original_text=original,
                confidence=0.9  # Normalization increased confidence
            )
        except Exception as e:
            logger.debug(f"SymPy parsing failed: {e}")
            return ExtractionResult(
                value=None,
                format="SYMPY_ERROR",
                original_text=original,
                confidence=0.0,
                error=str(e)
            )


# 전역 추출기 인스턴스
_GLOBAL_EXTRACTOR = AnswerExtractor()


def extract_answer_from_reasoning(reasoning_text: str) -> ExtractionResult:
    """
    추론 텍스트에서 답변을 추출합니다.
    
    Args:
        reasoning_text: 추론 텍스트
    
    Returns:
        ExtractionResult
    """
    global _GLOBAL_EXTRACTOR
    return _GLOBAL_EXTRACTOR.extract_from_text(reasoning_text)


def get_extractor() -> AnswerExtractor:
    """전역 추출기를 반환합니다."""
    global _GLOBAL_EXTRACTOR
    return _GLOBAL_EXTRACTOR
