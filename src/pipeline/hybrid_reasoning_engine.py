"""
Hybrid Reasoning Engine
- Mamba for long-context management (O(n) complexity)
- Transformer for precise local reasoning
- Graph-based problem decomposition
"""

import json
import re
from typing import List, Dict, Any, Optional
from collections import deque

class ReasoningChainManager:
    """
    긴 추론 체인을 효율적으로 관리
    - Long-term memory: 압축된 체크포인트 (Mamba 스타일)
    - Working memory: 최근 상세 스텝 (Transformer 처리용)
    """
    def __init__(self, max_working_steps: int = 5):
        self.long_context_memory = []
        self.working_memory = []
        self.max_working_steps = max_working_steps
        self.total_steps = 0
        
    def add_step(self, step: Dict):
        """새로운 추론 단계 추가 및 자동 압축"""
        self.working_memory.append(step)
        self.total_steps += 1
        
        # Working memory overflow → compress to long-term
        if len(self.working_memory) > self.max_working_steps:
            checkpoint = self._compress_checkpoint(self.working_memory[:3])
            self.long_context_memory.append(checkpoint)
            self.working_memory = self.working_memory[3:]
    
    def _compress_checkpoint(self, steps: List[Dict]) -> Dict:
        """
        여러 스텝을 하나의 체크포인트로 압축
        핵심 정보만 보존 (Mamba-style compression)
        """
        step_ids = [s.get('id', '') for s in steps]
        descriptions = [s.get('problem', s.get('description', '')) for s in steps]
        results = {s.get('id', f'step_{i}'): s.get('result', 'N/A') 
                  for i, s in enumerate(steps)}
        
        # 요약 생성
        summary = f"Steps {step_ids[0]}-{step_ids[-1]}: " + \
                 " → ".join([d[:30] + "..." if len(d) > 30 else d 
                            for d in descriptions])
        
        return {
            "checkpoint_id": len(self.long_context_memory) + 1,
            "summary": summary,
            "key_results": results,
            "step_range": (step_ids[0], step_ids[-1])
        }
    
    def get_context_for_next_step(self, include_long_term: bool = True) -> str:
        """
        다음 스텝용 컨텍스트 생성
        - Long-term: 압축된 요약 (개요)
        - Short-term: 상세한 최근 스텝
        """
        context_parts = []
        
        # Long-term memory (compressed summaries)
        if include_long_term and self.long_context_memory:
            lt_context = "\n".join([
                f"[Checkpoint {cp['checkpoint_id']}] {cp['summary']}"
                for cp in self.long_context_memory
            ])
            context_parts.append(f"Previous Work (Summary):\n{lt_context}")
        
        # Working memory (detailed recent steps)
        if self.working_memory:
            wm_context = "\n".join([
                f"Step {i+1}: {step.get('problem', step.get('description', 'N/A'))}\n"
                f"   Result: {step.get('result', 'Not solved')}"
                for i, step in enumerate(self.working_memory)
            ])
            context_parts.append(f"Recent Steps (Detailed):\n{wm_context}")
        
        return "\n\n".join(context_parts) if context_parts else "(No previous work)"
    
    def get_all_results(self) -> Dict[str, Any]:
        """모든 결과 수집 (최종 synthesis용)"""
        all_results = {}
        
        # Long-term checkpoints
        for cp in self.long_context_memory:
            all_results.update(cp['key_results'])
        
        # Working memory
        for step in self.working_memory:
            step_id = step.get('id', f'step_{self.working_memory.index(step)}')
            all_results[step_id] = step.get('result', 'N/A')
        
        return all_results


class ProblemGraph:
    """
    그래프 구조로 문제 표현
    - 명확한 의존성 관계
    - LLM이 이해하기 쉬운 구조
    """
    def __init__(self):
        self.nodes = []
        self.node_dict = {}
    
    def add_node(self, id: str, type: str, description: str = None, 
                 value: Any = None, dependencies: List[str] = None):
        """노드 추가"""
        node = {
            "id": id,
            "type": type,
            "description": description,
            "value": value,
            "dependencies": dependencies or [],
            "solved": False,
            "result": None,
            "code": None
        }
        self.nodes.append(node)
        self.node_dict[id] = node
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """노드 조회"""
        return self.node_dict.get(node_id)
    
    def mark_solved(self, node_id: str, result: Any, code: str = None):
        """노드를 해결됨으로 표시"""
        node = self.get_node(node_id)
        if node:
            node['solved'] = True
            node['result'] = result
            node['code'] = code
    
    def topological_sort(self) -> List[Dict]:
        """
        의존성 순서대로 정렬 (Kahn's algorithm)
        """
        # Calculate in-degrees
        in_degree = {node['id']: 0 for node in self.nodes}
        
        for node in self.nodes:
            for dep in node['dependencies']:
                if dep in in_degree:
                    in_degree[node['id']] += 1
        
        # Start with nodes having no dependencies
        queue = deque([node for node in self.nodes if in_degree[node['id']] == 0])
        sorted_nodes = []
        
        while queue:
            current = queue.popleft()
            sorted_nodes.append(current)
            
            # Reduce in-degree for dependent nodes
            for node in self.nodes:
                if current['id'] in node['dependencies']:
                    in_degree[node['id']] -= 1
                    if in_degree[node['id']] == 0:
                        queue.append(node)
        
        # Check for cycles
        if len(sorted_nodes) != len(self.nodes):
            raise ValueError("Circular dependency detected in problem graph!")
        
        return sorted_nodes
    
    def visualize(self) -> str:
        """그래프 시각화 (디버깅용)"""
        lines = ["=== Problem Dependency Graph ==="]
        for node in self.nodes:
            status = "✓" if node['solved'] else "○"
            deps = ", ".join(node['dependencies']) if node['dependencies'] else "None"
            lines.append(f"{status} {node['id']} [{node['type']}]")
            lines.append(f"   Description: {node['description']}")
            lines.append(f"   Depends on: {deps}")
            if node['solved']:
                lines.append(f"   Result: {node['result']}")
            lines.append("")
        return "\n".join(lines)


class SmartDecomposer:
    """
    LLM이 명확하게 이해할 수 있는 구조화된 분해 시스템
    """
    
    # 명시적 문제 타입 정의
    PROBLEM_TYPES = {
        "COMPUTE": "Calculate a specific numeric value",
        "FIND": "Find values satisfying conditions",
        "PROVE": "Prove a mathematical statement",
        "COUNT": "Count objects meeting criteria",
        "OPTIMIZE": "Find maximum/minimum values"
    }
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def decompose_to_graph(self, problem_text: str) -> ProblemGraph:
        """
        문제를 구조화된 그래프로 분해
        LLM에게 명확한 구조 제공
        """
        
        # Step 1: Extract structured information
        structured_prompt = f"""Analyze this math problem and extract:

1. GOAL: What is the final objective? (Choose type from: COMPUTE, FIND, PROVE, COUNT, OPTIMIZE)
2. GIVEN: What information is provided?
3. CONSTRAINTS: What conditions must be satisfied?
4. INTERMEDIATE_GOALS: What must be computed before the final answer?

Problem: {problem_text}

Respond in JSON format:
{{
  "goal": {{"type": "COMPUTE", "description": "final answer description"}},
  "given": ["fact 1", "fact 2"],
  "constraints": ["constraint 1"],
  "intermediate_goals": [
    {{"id": "IG1", "type": "COMPUTE", "description": "...", "depends_on": []}},
    {{"id": "IG2", "type": "FIND", "description": "...", "depends_on": ["IG1"]}}
  ]
}}
"""
        
        response = self.llm.generate(structured_prompt)
        structure = self._extract_and_parse_json(response)
        
        # Step 2: Build graph
        graph = ProblemGraph()
        
        # Add GIVEN nodes (starting points)
        for i, given in enumerate(structure.get('given', [])):
            graph.add_node(
                id=f"GIVEN_{i+1}",
                type="GIVEN",
                description=given,
                value=given,
                dependencies=[]
            )
        
        # Add intermediate goal nodes
        for ig in structure.get('intermediate_goals', []):
            graph.add_node(
                id=ig['id'],
                type=ig['type'],
                description=ig['description'],
                dependencies=ig.get('depends_on', [])
            )
        
        # Add final goal node
        final_goal = structure.get('goal', {})
        all_ig_ids = [ig['id'] for ig in structure.get('intermediate_goals', [])]
        graph.add_node(
            id="FINAL",
            type=final_goal.get('type', 'COMPUTE'),
            description=final_goal.get('description', 'Final answer'),
            dependencies=all_ig_ids
        )
        
        return graph
    
    def _extract_and_parse_json(self, response: str) -> Dict:
        """LLM 응답에서 JSON 추출 및 파싱"""
        # Try to find JSON in markdown block
        match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # Try to find raw JSON
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                # Fallback: return empty structure
                return {
                    "goal": {"type": "COMPUTE", "description": "solve the problem"},
                    "given": [],
                    "constraints": [],
                    "intermediate_goals": []
                }
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse JSON from LLM response")
            return {
                "goal": {"type": "COMPUTE", "description": "solve the problem"},
                "given": [],
                "constraints": [],
                "intermediate_goals": []
            }
    
    def generate_prompt_for_node(self, node: Dict, graph: ProblemGraph, 
                                 context_manager: ReasoningChainManager) -> str:
        """
        각 노드를 LLM이 이해할 수 있는 명확한 프롬프트로 변환
        """
        if node['type'] == "GIVEN":
            return None  # GIVEN nodes don't need solving
        
        # Collect dependency results
        deps_context = []
        for dep_id in node['dependencies']:
            dep_node = graph.get_node(dep_id)
            if dep_node and dep_node['solved']:
                deps_context.append(
                    f"{dep_id} ({dep_node['type']}): {dep_node['result']}"
                )
        
        # Get historical context from chain manager
        historical_context = context_manager.get_context_for_next_step()
        
        # Type-specific prompt template
        template = self._get_template_for_type(node['type'])
        
        prompt = template.format(
            node_id=node['id'],
            description=node['description'],
            dependencies="\n".join(deps_context) if deps_context else "None",
            problem_type=self.PROBLEM_TYPES.get(node['type'], "Unknown"),
            historical_context=historical_context
        )
        
        return prompt
    
    def _get_template_for_type(self, node_type: str) -> str:
        """각 문제 타입에 맞는 명확한 프롬프트 템플릿"""
        templates = {
            "COMPUTE": """=== Task ID: {node_id} ===
Type: COMPUTE - {problem_type}
Goal: {description}

Known Values:
{dependencies}

Historical Context:
{historical_context}

Write Python code to COMPUTE the exact numeric value. Print ONLY the final result.""",
            
            "FIND": """=== Task ID: {node_id} ===
Type: FIND - {problem_type}
Goal: {description}

Known Values:
{dependencies}

Historical Context:
{historical_context}

Write Python code to FIND all values satisfying the conditions. Print all solutions.""",
            
            "PROVE": """=== Task ID: {node_id} ===
Type: PROVE - {problem_type}
Goal: {description}

Known Values:
{dependencies}

Historical Context:
{historical_context}

Write Python code to VERIFY this statement. Print True or False with brief reasoning.""",
            
            "COUNT": """=== Task ID: {node_id} ===
Type: COUNT - {problem_type}
Goal: {description}

Known Values:
{dependencies}

Historical Context:
{historical_context}

Write Python code to COUNT the objects. Print the count as an integer.""",
            
            "OPTIMIZE": """=== Task ID: {node_id} ===
Type: OPTIMIZE - {problem_type}
Goal: {description}

Known Values:
{dependencies}

Historical Context:
{historical_context}

Write Python code to find the OPTIMAL value. Print the maximum or minimum value."""
        }
        
        return templates.get(node_type, templates["COMPUTE"])


class HybridReasoningEngine:
    """
    통합 추론 엔진
    - SmartDecomposer: 문제를 그래프로 분해
    - ReasoningChainManager: 긴 추론 체인 관리
    - Solver + Executor: 각 노드 실행
    """
    def __init__(self, solver, executor):
        self.solver = solver
        self.executor = executor
        self.decomposer = SmartDecomposer(self.solver.llm)
        self.chain_manager = ReasoningChainManager(max_working_steps=5)
    
    def solve_with_graph(self, problem_text: str) -> str:
        """
        그래프 기반 구조화된 문제 해결
        """
        print("\n=== Hybrid Reasoning Engine ===")
        
        # Step 1: Decompose to graph
        print("1. Decomposing problem to graph...")
        graph = self.decomposer.decompose_to_graph(problem_text)
        print(graph.visualize())
        
        # Step 2: Solve nodes in topological order
        print("\n2. Solving nodes in dependency order...")
        sorted_nodes = graph.topological_sort()
        
        for node in sorted_nodes:
            if node['type'] == 'GIVEN':
                # Mark as solved immediately
                graph.mark_solved(node['id'], node['value'])
                continue
            
            print(f"\n   Solving {node['id']} [{node['type']}]...")
            
            # Generate prompt with full context
            prompt = self.decomposer.generate_prompt_for_node(
                node, graph, self.chain_manager
            )
            
            # Generate and execute code
            code = self.solver.generate_code_from_prompt(prompt)
            result = self.executor.execute(code)
            
            if "Error" not in result:
                # Success
                graph.mark_solved(node['id'], result.strip(), code)
                print(f"   ✅ Result: {result.strip()}")
                
                # Add to chain manager
                self.chain_manager.add_step({
                    "id": node['id'],
                    "problem": node['description'],
                    "result": result.strip(),
                    "code": code
                })
            else:
                # Error
                print(f"   ❌ Error: {result[:100]}")
                graph.mark_solved(node['id'], "ERROR", code)
        
        # Step 3: Extract final answer
        print("\n3. Extracting final answer...")
        final_node = graph.get_node("FINAL")
        
        if final_node and final_node['solved'] and final_node['result'] != "ERROR":
            print(f"\n✅ Final Answer: {final_node['result']}")
            return final_node['result']
        else:
            print("\n❌ Failed to solve problem")
            return None


# Helper function for Solver class
def generate_code_from_prompt(solver_instance, prompt: str) -> str:
    """
    Solver에 추가할 헬퍼 메서드
    이미 구조화된 프롬프트를 받아서 코드만 생성
    """
    response = solver_instance.llm.generate(prompt)
    return solver_instance._extract_code(response)
