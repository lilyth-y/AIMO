"""
Interface Adapter for AIMO 3 Gateway
- Handles communication between Kaggle Gateway and Pipeline Orchestrator
- Manages data transformation (DataFrame <-> Dict)
"""

import sys
import pandas as pd
import polars as pl
from typing import Any

# Note: sys.path manipulation is generally not recommended
# Consider using proper package structure instead

from .orchestrator import PipelineOrchestrator
from .stage1_labeling import ProblemAnalyzer
from .logger import get_logger

logger = get_logger()

class AIMOInterface:
    """
    AIMO 3 Gateway Interface
    
    Kaggle Gateway와 Pipeline Orchestrator 간의 통신을 처리합니다.
    DataFrame과 Dict 간의 데이터 변환을 관리합니다.
    """
    
    def __init__(self) -> None:
        """
        AIMOInterface 초기화
        
        Orchestrator와 ProblemAnalyzer를 초기화합니다.
        """
        self.orchestrator = PipelineOrchestrator()
        self.analyzer = ProblemAnalyzer()
        self.total_problems = 50  # Estimated, usually 50 for AIMO
        self.solved_count = 0

    def predict(self, id_series: pl.Series, problem_series: pl.Series) -> pl.DataFrame:
        """
        Called by the Gateway for each problem batch.
        Args:
            id_series: Polars Series containing the ID (length 1)
            problem_series: Polars Series containing the problem text (length 1)
        """
        # 1. Extract Problem
        try:
            problem_id = id_series.item(0)
            problem_text = problem_series.item(0)
        except Exception as e:
            logger.error(f"Error extracting data from series: {e}")
            return pl.DataFrame({'answer': [0]})

        logger.info(f"Received Problem ID: {problem_id}")
        
        # 2. Analyze Problem (Stage 1)
        # We do this here to pass structured info to Orchestrator
        domain = self.analyzer.classify_domain(problem_text)
        variables = self.analyzer.extract_variables(problem_text)
        
        # 3. Calculate Time Budget (Simple Heuristic)
        # In a real scenario, we would track elapsed time
        self.solved_count += 1
        remaining = self.total_problems - self.solved_count
        # time_budget = calculate_budget(remaining) 
        
        # 4. Delegate to Orchestrator
        try:
            result = self.orchestrator.solve_problem(domain, variables, problem_text)
            answer = result.get('answer') if isinstance(result, dict) else result
        except Exception as e:
            logger.error(f"Error in orchestrator: {e}", exc_info=True)
            answer = None
        
        # 5. Fallback for absolute failure (should be rare)
        if answer is None:
            answer = 0 # Default safe answer or random guess
            
        # 6. Format Response
        # Ensure answer is an integer within range (0-99999) is handled by Stage 5,
        # but we do a final safety cast here.
        try:
            final_answer = int(answer) % 100000
        except (ValueError, TypeError):
            final_answer = 0
            
        return pl.DataFrame({'answer': [final_answer]})

# Global instance for the Gateway to use
interface = AIMOInterface()

def predict(id_series: pl.Series, problem_series: pl.Series):
    """
    The actual callback function expected by the InferenceServer.
    Must be named 'predict' to match the Gateway's call.
    """
    return interface.predict(id_series, problem_series)
