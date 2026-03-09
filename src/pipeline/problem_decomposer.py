"""
Problem Decomposition Module
- Breaks down complex problems into manageable sub-problems
- Tracks dependencies between sub-problems
- Synthesizes final answer from sub-solutions
"""

from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .solver import Solver
    from .executor import CodeExecutor
import re

class SubProblem:
    def __init__(self, id: str, description: str, dependencies: List[str] = None):
        self.id = id
        self.description = description
        self.dependencies = dependencies or []
        self.solution = None
        self.solved = False

class ProblemDecomposer:
    """
    Decomposes complex problems using LLM-guided analysis.
    """
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def analyze_problem(self, problem_text: str) -> Dict[str, Any]:
        """
        Analyze problem to determine if decomposition is needed.
        Returns problem type and complexity assessment.
        """
        analysis_prompt = f"""Analyze this math problem and determine:
1. Problem Type: [computational, geometric, proof, algebraic, combinatorial, mixed]
2. Complexity: [simple, moderate, complex]
3. Needs Decomposition: [yes/no]
4. Key Concepts: [list main mathematical concepts]

Problem: {problem_text}

Respond in this format:
Type: <type>
Complexity: <level>
Decompose: <yes/no>
Concepts: <concept1>, <concept2>, ...
Reasoning: <brief explanation>
"""
        
        response = self.llm.generate(analysis_prompt)
        return self._parse_analysis(response)
    
    def decompose(self, problem_text: str) -> List[SubProblem]:
        """
        Break down complex problem into sub-problems.
        """
        decomposition_prompt = f"""Break down this complex math problem into logical sub-problems.
For each sub-problem:
- Give it an ID (SP1, SP2, etc.)
- Describe what needs to be solved
- List dependencies (which sub-problems must be solved first)

Problem: {problem_text}

Format your response as:
SP1: <description>
Dependencies: none
---
SP2: <description>
Dependencies: SP1
---
...

Make sure to:
1. Create sub-problems that are individually solvable
2. Maintain logical flow from simple to complex
3. Identify all dependencies clearly
"""
        
        response = self.llm.generate(decomposition_prompt)
        return self._parse_subproblems(response)
    
    def solve_hierarchically(self, problem_text: str, solver: 'Solver', executor: 'CodeExecutor') -> Any:
        """
        Solve problem by decomposing and solving sub-problems in order.
        NOW EXECUTES CODE AND PASSES ACTUAL RESULTS AS CONTEXT!
        """
        # 1. Analyze problem
        analysis = self.analyze_problem(problem_text)
        
        # 2. If simple, solve directly
        if analysis.get('decompose') == 'no':
            # Direct solve: generate code then execute
            code = solver.generate_code(problem_text, "Path C: The Hybrid")
            exec_result = executor.execute(code)
            return {
                'mode': 'direct',
                'code': code,
                'result': exec_result.strip()
            }
        
        # 3. Decompose into sub-problems
        sub_problems = self.decompose(problem_text)
        
        # 4. Solve in dependency order WITH EXECUTION
        solved_context = {}  # Stores EXECUTED RESULTS
        conversation_history = []  # Track full conversation for context
        
        for sp in self._topological_sort(sub_problems):
            # Build context from solved dependencies (now includes actual values!)
            context = self._build_context(sp, solved_context)
            
            # Include conversation history for deeper context
            history_text = "\n\n".join([
                f"Previous Step: {step['problem']}\nSolution: {step['result']}"
                for step in conversation_history[-3:]  # Last 3 steps
            ])
            
            # Solve this sub-problem with FULL CONTEXT
            sp_prompt = f"""Original Problem Context: {problem_text}

Previous Steps:
{history_text if history_text else 'This is the first step.'}

Known Values:
{context}

Current Sub-Problem:
{sp.description}

Write Python code to solve this specific sub-problem. You can use the known values above.
The code must print the final answer."""
            
            # Generate code
            code = solver.generate_code(sp_prompt, "Path C: The Hybrid")
            
            # EXECUTE CODE TO GET ACTUAL RESULT
            from .stage4_execution import CodeExecutor
            exec_result = executor.execute(code)
            
            # Store both code and EXECUTED RESULT
            if "Error" not in exec_result:
                result_value = exec_result.strip()
                sp.solution = {"code": code, "result": result_value}
                sp.solved = True
                solved_context[sp.id] = {
                    "description": sp.description,
                    "result": result_value
                }
                conversation_history.append({
                    "problem": sp.description,
                    "code": code,
                    "result": result_value
                })
                print(f"   ✅ {sp.id} solved: {result_value}")
            else:
                print(f"   ❌ {sp.id} failed: {exec_result[:100]}")
                sp.solution = {"code": code, "result": None}
                sp.solved = False
        
        # 5. Synthesize final answer using ACTUAL RESULTS
        return self._synthesize_answer(problem_text, sub_problems, solved_context, conversation_history, executor)
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Parse LLM analysis response."""
        analysis = {}
        lines = response.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                analysis[key.strip().lower()] = value.strip()
        return analysis
    
    def _parse_subproblems(self, response: str) -> List[SubProblem]:
        """Parse sub-problems from LLM response."""
        sub_problems = []
        blocks = response.strip().split('---')
        
        for block in blocks:
            if not block.strip():
                continue
            
            lines = block.strip().split('\n')
            sp_id = None
            description = None
            dependencies = []
            
            for line in lines:
                if line.startswith('SP'):
                    parts = line.split(':', 1)
                    sp_id = parts[0].strip()
                    description = parts[1].strip() if len(parts) > 1 else ""
                elif 'Dependencies:' in line:
                    dep_text = line.split(':', 1)[1].strip()
                    if dep_text.lower() != 'none':
                        dependencies = [d.strip() for d in dep_text.split(',')]
            
            if sp_id and description:
                sub_problems.append(SubProblem(sp_id, description, dependencies))
        
        return sub_problems
    
    def _topological_sort(self, sub_problems: List[SubProblem]) -> List[SubProblem]:
        """Sort sub-problems by dependencies (topological sort)."""
        # Simple implementation - for production use proper topological sort
        sorted_sps = []
        remaining = sub_problems.copy()
        
        while remaining:
            # Find sub-problems with no unsolved dependencies
            ready = [sp for sp in remaining 
                    if all(dep not in [r.id for r in remaining] 
                          for dep in sp.dependencies)]
            
            if not ready:
                # Circular dependency or error - return what we have
                return sorted_sps + remaining
            
            sorted_sps.extend(ready)
            for sp in ready:
                remaining.remove(sp)
        
        return sorted_sps
    
    def _build_context(self, sp: SubProblem, solved_context: Dict[str, Any]) -> str:
        """Build context string from solved dependencies WITH ACTUAL VALUES."""
        if not sp.dependencies:
            return "No previous values needed - this is an independent sub-problem."
        
        context_parts = []
        for dep_id in sp.dependencies:
            if dep_id in solved_context:
                dep_info = solved_context[dep_id]
                if isinstance(dep_info, dict):
                    context_parts.append(
                        f"{dep_id} ({dep_info['description']}): {dep_info['result']}"
                    )
                else:
                    context_parts.append(f"{dep_id}: {dep_info}")
        
        if not context_parts:
            return "Dependencies not yet solved."
        
        return "\n".join(context_parts)
    
    def _synthesize_answer(self, original_problem: str, 
                          sub_problems: List[SubProblem], 
                          solved_context: Dict[str, Any],
                          conversation_history: List[Dict],
                          executor) -> Any:
        """Synthesize final answer from sub-problem solutions WITH FULL CONTEXT."""
        
        # Build comprehensive solution summary
        solutions_summary = []
        for sp in sub_problems:
            if sp.solved and sp.solution:
                result = sp.solution.get('result', 'N/A')
                solutions_summary.append(f"{sp.id} - {sp.description}\n   Result: {result}")
        
        synthesis_prompt = f"""Original Problem:
{original_problem}

Step-by-Step Solutions:
{chr(10).join(solutions_summary)}

All the sub-problems have been solved. Now write Python code to:
1. Use the results above to compute the FINAL ANSWER to the original problem
2. Print only the final answer

The code should use the known values and perform any final calculations needed."""
        
        final_code = self.llm.generate(synthesis_prompt)
        match = re.search(r'```python(.*?)```', final_code, re.DOTALL)
        code_block = match.group(1).strip() if match else final_code.strip()
        exec_result = executor.execute(code_block)
        return {
            'mode': 'hierarchical',
            'code': code_block,
            'result': exec_result.strip(),
            'steps': [
                {
                    'id': sp.id,
                    'desc': sp.description,
                    'result': (sp.solution or {}).get('result') if sp.solution else None
                } for sp in sub_problems
            ]
        }
