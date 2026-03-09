"""
문제 다양성 분석 스크립트
데이터셋의 문제 유형과 종류의 다양성을 분석합니다.
"""

import sys
import json
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.problem_diversity import ProblemDiversityAnalyzer, analyze_problem_diversity


def load_problems_from_jsonl(file_path: Path) -> list:
    """JSONL 파일에서 문제를 로드합니다."""
    problems = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                problem_data = json.loads(line)
                problems.append(problem_data)
            except json.JSONDecodeError:
                continue
    return problems


def load_problems_from_json(file_path: Path) -> list:
    """JSON 파일에서 문제를 로드합니다."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 리스트인 경우 그대로 반환
    if isinstance(data, list):
        return data
    
    # 딕셔너리인 경우 'problems' 키 확인
    if isinstance(data, dict) and 'problems' in data:
        return data['problems']
    
    # 단일 문제인 경우
    return [data]


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='문제 다양성 분석')
    parser.add_argument('--input', type=str, default='data/eval_data.jsonl',
                       help='입력 파일 경로 (JSONL 또는 JSON)')
    parser.add_argument('--output', type=str, default='docs/problem_diversity_report.txt',
                       help='출력 보고서 파일 경로')
    parser.add_argument('--json-output', type=str, default=None,
                       help='JSON 형식 출력 파일 경로 (선택적)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    print(f"문제 파일 로딩: {input_path}")
    
    # 파일 형식에 따라 로드
    if input_path.suffix == '.jsonl':
        problems = load_problems_from_jsonl(input_path)
    elif input_path.suffix == '.json':
        problems = load_problems_from_json(input_path)
    else:
        print(f"지원하지 않는 파일 형식: {input_path.suffix}")
        return
    
    print(f"로드된 문제 수: {len(problems)}")
    
    if len(problems) == 0:
        print("❌ 문제가 없습니다.")
        return
    
    # 다양성 분석
    print("\n문제 다양성 분석 중...")
    result = analyze_problem_diversity(problems, output_path)
    
    # 보고서 출력 (UTF-8 인코딩)
    import sys
    if sys.stdout.encoding != 'utf-8':
        # Windows 콘솔 인코딩 문제 해결
        report_text = result['report'].encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        print("\n" + report_text)
    else:
        print("\n" + result['report'])
    
    # JSON 출력 (선택적)
    if args.json_output:
        json_path = Path(args.json_output)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result['analysis'], f, indent=2, ensure_ascii=False)
        print(f"\nJSON 결과 저장: {json_path}")
    
    # 검증 결과
    if result['is_valid']:
        print("\n✅ 다양성 검증 통과!")
    else:
        print("\n❌ 다양성 검증 실패 - 보고서를 확인하세요.")


if __name__ == "__main__":
    main()
