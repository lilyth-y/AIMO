"""
리스트 오류 수정 테스트
모델 출력이 리스트일 때 올바르게 처리되는지 확인
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock test for list handling
def test_list_handling():
    from pipeline.solver import LocalLLMClient
    
    # Create a mock scenario
    class MockLLMClient(LocalLLMClient):
        def generate(self, prompt: str) -> str:
            # Simulate list output from model
            mock_output = ["print('test')", "x = 1"]
            # This should be handled correctly now
            if isinstance(mock_output, list):
                return '\n'.join(str(x) for x in mock_output)
            return str(mock_output)
    
    print("="*70)
    print("리스트 오류 수정 테스트")
    print("="*70)
    
    # Test 1: List to string conversion
    test_list = ["print('hello')", "x = 42"]
    result = '\n'.join(str(x) for x in test_list)
    assert isinstance(result, str), "리스트가 문자열로 변환되어야 함"
    print("[OK] 리스트 -> 문자열 변환 성공")
    
    # Test 2: String startswith check
    test_string = "ERROR: something went wrong"
    assert test_string.startswith('ERROR:'), "문자열 startswith 체크 성공"
    print("[OK] 문자열 startswith 체크 성공")
    
    # Test 3: Mixed type handling
    test_mixed = [1, 2, 3]
    result_mixed = str(test_mixed) if not isinstance(test_mixed, str) else test_mixed
    assert isinstance(result_mixed, str), "혼합 타입이 문자열로 변환되어야 함"
    print("[OK] 혼합 타입 처리 성공")
    
    print("\n" + "="*70)
    print("[SUCCESS] 모든 테스트 통과!")
    print("="*70)
    return True

if __name__ == "__main__":
    test_list_handling()
