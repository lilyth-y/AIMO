"""
Difficulty Metrics Module
- Defines the dimensions of mathematical difficulty for generated problems.
- Used to score and categorize problems based on their structural complexity.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DifficultyScore:
    level: int  # 1 (Easy) to 5 (Olympiad)
    metrics: 'DifficultyMetrics'
    description: str

@dataclass
class DifficultyMetrics:
    # 1. Logical Depth (추론 단계 수)
    # Minimum number of logical steps required to reach the solution.
    # e.g., 1 step: Formula application. 3+ steps: Multi-stage deduction.
    reasoning_steps: int

    # 2. Concept Coupling (결합된 개념 수)
    # Number of distinct mathematical domains interacting.
    # e.g., Algebra + Number Theory (Integer solutions to equations).
    concept_count: int

    # 3. Branching Factor (분기 계수 / 경우의 수)
    # Does the solution require splitting into cases?
    # 1: Linear path. >1: Case analysis required (e.g., absolute values, modular cases).
    branching_factor: int

    # 4. Intermediate Abstraction (중간 보조항 생성)
    # Does the solver need to introduce variables not present in the problem statement?
    # e.g., "Let total work be W", "Let gcd(a,b) = g".
    requires_auxiliary_variable: bool

    # 5. Implicit Constraints (암묵적 제약 조건)
    # Are there constraints hidden in the context?
    # e.g., "Integer" (from 'people'), "Distinct" (from 'set'), "Positive".
    implicit_constraints: List[str]

    def calculate_total_score(self) -> int:
        """
        Calculates a heuristic difficulty score (0-100).
        """
        score = 0
        score += self.reasoning_steps * 10
        score += self.concept_count * 15
        score += (self.branching_factor - 1) * 20
        score += 25 if self.requires_auxiliary_variable else 0
        score += len(self.implicit_constraints) * 5
        return score

# Example Definitions of Difficulty Levels
DIFFICULTY_EXAMPLES = {
    "Level 1 (Elementary)": DifficultyMetrics(
        reasoning_steps=1,
        concept_count=1,
        branching_factor=1,
        requires_auxiliary_variable=False,
        implicit_constraints=[]
    ),
    "Level 3 (AIME Mid)": DifficultyMetrics(
        reasoning_steps=4,
        concept_count=2,  # e.g., Combinatorics + Number Theory
        branching_factor=2,  # e.g., Case 1: x is even, Case 2: x is odd
        requires_auxiliary_variable=True,  # "Let N = 10a + b"
        implicit_constraints=["Integer", "Distinct"]
    ),
    "Level 5 (Olympiad High)": DifficultyMetrics(
        reasoning_steps=8,
        concept_count=3,  # e.g., Geometry + Algebra + Inequalities
        branching_factor=4,  # Complex case analysis
        requires_auxiliary_variable=True,  # Auxiliary lines or functions
        implicit_constraints=["Prime", "Coprime", "Geometric Bounds"]
    )
}
