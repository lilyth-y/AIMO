"""
MCP 결과 평가 스크립트
통합 평가 유틸리티를 사용하여 결과를 평가합니다.
"""

import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from evaluation.evaluation_utils import (
    EvaluationMetrics, EvaluationResult,
    check_answer_correctness
)

def evaluate_mcp_results(input_file='mcp_results.json', output_file=None):
    """
    MCP 결과 파일을 평가합니다.
    
    Args:
        input_file: 입력 JSON 파일 경로
        output_file: 출력 파일 경로 (None이면 자동 생성)
    """
    with open(input_file, encoding='utf-8') as f:
        results = json.load(f)
    
    metrics = EvaluationMetrics(dataset_name="MCP_Results")
    metrics.start()
    
    total = len(results)
    success = 0
    has_answer = 0
    
    for idx, entry in enumerate(results):
        result_data = entry.get('result', {})
        problem_data = entry.get('problem', {})
        answer = problem_data.get('answer')
        output = result_data.get('output')
        error = result_data.get('error')
        problem_text = problem_data.get('description', '')
        
        # 코드 실행 성공 여부
        execution_success = (error is None and output is not None)
        if execution_success:
            success += 1
        
        # 정답 검증
        is_correct = False
        if answer is not None and execution_success:
            has_answer += 1
            is_correct = check_answer_correctness(answer, output)
        
        # 결과 저장
        eval_result = EvaluationResult(
            problem_id=idx,
            problem=problem_text,
            reference_answer=str(answer) if answer is not None else None,
            predicted_answer=str(output) if output is not None else None,
            is_correct=is_correct,
            error=str(error) if error else None,
            metadata={
                'execution_success': execution_success,
                'has_reference_answer': answer is not None
            }
        )
        
        metrics.add_result(eval_result)
    
    metrics.finish()
    
    # 요약 출력
    print(f'\n{"="*70}')
    print(f'총 문제 수: {total}')
    print(f'코드 실행 성공률: {success/total:.2%} ({success}/{total})')
    
    if has_answer > 0:
        final_metrics = metrics.calculate_metrics()
        print(f'정답 일치율(정답이 있는 문제 기준): {final_metrics["accuracy"]:.2%}')
    else:
        print('정답이 포함된 문제가 없습니다.')
    
    print(f'{"="*70}\n')
    
    # 상세 요약 출력
    metrics.print_summary()
    
    # 결과 저장
    if output_file is None:
        output_file = 'results/mcp_evaluation_results.json'
    
    output_path = metrics.save_results(
        output_dir='results',
        filename=os.path.basename(output_file)
    )
    
    print(f'결과가 저장되었습니다: {output_path}')
    
    return metrics

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP 결과 평가')
    parser.add_argument('--input', type=str, default='mcp_results.json',
                        help='입력 JSON 파일 경로')
    parser.add_argument('--output', type=str, default=None,
                        help='출력 파일 경로 (기본값: results/mcp_evaluation_results.json)')
    args = parser.parse_args()
    
    evaluate_mcp_results(args.input, args.output)
