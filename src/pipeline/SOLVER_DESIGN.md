# AIMO 3 Solver Logic Design

## Overview
The Solver Engine is the core intelligence of the pipeline. It translates the strategic plan (from the Router) into executable Python code using an LLM.

## Architecture

### 1. Prompt Engineering Strategy
We use a **Role-Task-Context** prompting framework.

#### A. The Simulator Prompt (Brute Force)
*   **Role**: "You are an expert Python programmer specializing in numerical simulations."
*   **Task**: "Write a Python script to solve the following problem by iterating through all possible cases. Ensure the code is efficient enough to run within 5 seconds for N < 10^6."
*   **Output**: Python code block.

#### B. The Theoretician Prompt (SymPy/Math)
*   **Role**: "You are a computational mathematician expert in SymPy."
*   **Task**: "Solve this problem analytically using the SymPy library. Output the final answer as a printed integer."
*   **Output**: Python code block using `sympy.symbols`, `sympy.solve`, etc.

#### C. The Hybrid Prompt (Decomposition)
*   **Role**: "You are a creative problem solver."
*   **Task**: "This problem is too large for direct simulation. Decompose it into smaller sub-problems, solve them using Python, and combine the results."
*   **Output**: Python code block.

### 2. Self-Correction (Traceback Analysis)
When execution fails, the `Orchestrator` captures the traceback and feeds it back to the Solver.

*   **Prompt**: "The previous code failed with the following error: `{error_msg}`.
    Here is the code:
    ```python
    {original_code}
    ```
    Fix the error and output the corrected code."

### 3. Verification Logic
To prevent "hallucinations", we employ a **Dual-Verification** system.

1.  **Format Check**: Ensure output is an integer modulo 1000 (or 5-digit as per competition rules).
2.  **Reverse Check**:
    *   The Solver is asked to generate a *Verification Script* alongside the solution.
    *   Example: If $x=5$, the verification script checks if $2(5)+3=13$.
    *   If the verification script returns `False`, the solution is discarded.

## Implementation Plan
1.  **`LLMClient`**: Abstract class for API calls (OpenAI, Anthropic, vLLM).
2.  **`PromptFactory`**: Class to generate dynamic prompts based on Strategy and Problem Type.
3.  **`Parser`**: Robust regex to extract code blocks and handle markdown formatting issues.

## Current State (Mock)
A `MockLLM` is currently implemented in `src/pipeline/solver.py` to simulate this behavior for the provided test cases (`test.csv`). This allows end-to-end pipeline testing without consuming API credits.
