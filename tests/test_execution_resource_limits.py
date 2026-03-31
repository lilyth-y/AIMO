"""
실행 리소스 제한 테스트
CPU 시간, 메모리, 타임아웃 제한을 테스트합니다.
"""

import pytest
import time
from src.pipeline.stage4_execution import CodeExecutor

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@pytest.mark.slow
class TestExecutionResourceLimits:
    """실행 리소스 제한 테스트"""
    
    def test_timeout(self):
        """타임아웃 테스트"""
        executor = CodeExecutor(timeout_seconds=1.0)
        
        # 무한 루프 코드
        infinite_loop = "while True: pass"
        result = executor.execute(infinite_loop)
        
        assert "Error: Timeout" in result or "Error" in result
    
    def test_memory_limit(self):
        """메모리 제한 테스트"""
        if not PSUTIL_AVAILABLE:
            pytest.skip("psutil not available")
        
        executor = CodeExecutor(memory_limit_mb=10)  # 매우 낮은 제한
        
        # 메모리를 많이 사용하는 코드
        memory_hog = """
data = []
for i in range(1000000):
    data.append([0] * 1000)
"""
        result = executor.execute(memory_hog)
        
        # 메모리 제한 초과 또는 타임아웃
        assert "Error" in result
    
    def test_cpu_time_limit(self):
        """CPU 시간 제한 테스트"""
        if not PSUTIL_AVAILABLE:
            pytest.skip("psutil not available")
        
        executor = CodeExecutor(cpu_time_limit_sec=0.5)  # 매우 낮은 제한
        
        # CPU를 많이 사용하는 코드
        cpu_intensive = """
import math
result = 0
for i in range(10000000):
    result += math.sqrt(i)
"""
        result = executor.execute(cpu_intensive)
        
        # CPU 시간 제한 초과 또는 타임아웃
        assert "Error" in result
    
    def test_normal_execution(self):
        """정상 실행 테스트"""
        executor = CodeExecutor(timeout_seconds=5.0)
        
        code = """
x = 10 + 20
print(f"Result: {x}")
"""
        result = executor.execute(code)
        
        assert "Result: 30" in result
        assert "Error" not in result
    
    def test_execute_with_stats(self):
        """통계 포함 실행 테스트"""
        executor = CodeExecutor(timeout_seconds=2.0)
        
        code = """
for i in range(100):
    x = i * 2
print("Done")
"""
        result, stats = executor.execute_with_stats(code)
        
        assert "Done" in result
        assert "wall_ms" in stats
        assert "mem_mb" in stats
        assert "cpu_ms" in stats
        assert stats["wall_ms"] > 0
    
    def test_forbidden_patterns(self):
        """금지된 패턴 테스트"""
        executor = CodeExecutor()
        
        # 금지된 import
        forbidden_code = "import os"
        result = executor.execute(forbidden_code)
        
        assert "Error: Forbidden pattern" in result
    
    def test_static_check(self):
        """정적 검사 테스트"""
        executor = CodeExecutor()
        
        # 금지된 서브스트링
        test_cases = [
            ("import os", True),
            ("import sys", True),
            ("subprocess.call", True),
            ("print('hello')", False),  # 허용된 코드
        ]
        
        for code, should_fail in test_cases:
            result = executor.execute(code)
            if should_fail:
                assert "Error: Forbidden pattern" in result, f"Failed to detect forbidden pattern in: {code}"
            else:
                assert "Error: Forbidden pattern" not in result, f"False positive for: {code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
