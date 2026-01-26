from typing import Any, Optional, Dict
from dataclasses import dataclass
from .stage5_verification import VerificationRouter

@dataclass
class ReconciliationResult:
    match: bool
    status: str  # 'MATCH', 'MISMATCH_FORMAT', 'MISMATCH_VALUE', 'ERROR_PARSING'
    details: str = ""

class ReasoningReconciler:
    def __init__(self, verifier: Optional[VerificationRouter] = None):
        self.verifier = verifier if verifier else VerificationRouter()

    def reconcile(self, extracted_answer: Any, execution_result: Any) -> ReconciliationResult:
        """
        Reconciles the answer extracted from reasoning text (e.g. <ANS>) 
        with the result from code execution.
        """
        if extracted_answer is None or execution_result is None:
             return ReconciliationResult(False, 'ERROR_MISSING', "One of the answers is None")

        # 1. Parse both to comparable forms
        parsed_ex = self.verifier._parse_answer(extracted_answer)
        parsed_exec = self.verifier._parse_answer(execution_result)

        if parsed_ex is None or parsed_exec is None:
            return ReconciliationResult(False, 'ERROR_PARSING', f"Cannot parse: Ex='{extracted_answer}', Exec='{execution_result}'")

        # 2. Check for Equivalence (using robust VerificationRouter logic)
        if self.verifier._compare(parsed_ex, parsed_exec):
            # If they compare equal, check if string representation is different (Format Mismatch)
            if str(extracted_answer).strip() != str(execution_result).strip():
                return ReconciliationResult(True, 'MATCH_FORMAT_DIFF', "Values match but formats differ")
            return ReconciliationResult(True, 'MATCH_EXACT', "Exact match")

        # 3. If not equal, classify mismatch
        # Try to see if they are numeric but different
        is_num_ex = isinstance(parsed_ex, (int, float))
        is_num_exec = isinstance(parsed_exec, (int, float))
        
        if is_num_ex and is_num_exec:
            return ReconciliationResult(False, 'MISMATCH_ARITHMETIC', f"Numeric difference: {parsed_ex} vs {parsed_exec}")
        
        return ReconciliationResult(False, 'MISMATCH_LOGIC', f"Structural/Logic mismatch: {parsed_ex} vs {parsed_exec}")
