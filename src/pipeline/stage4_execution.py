"""Stage 4: Execution & Error Correction (고급 리소스 제한)

개선:
 - 멀티프로세스 기반 타임아웃 (Windows 호환)
 - CPU 시간 및 메모리 실시간 감시
 - 기본 stdout 캡처
 - 강화된 안전 필터 (위험한 내장 / 파일 I/O 차단)
 - 무한 루프 방지
주의: 완전한 샌드박스 아님 (프로덕션에서는 별도 격리 필요)
"""

from io import StringIO
import multiprocessing as mp
import contextlib
import builtins
import time
import os
import signal
from typing import Optional, Dict, Any, Tuple
from .logger import get_logger

logger = get_logger()

try:
    import psutil  # optional for resource stats
except ImportError:
    psutil = None
    logger.warning("psutil not available - resource monitoring will be limited")

DEFAULT_MEMORY_LIMIT_MB = int(os.getenv("AIMO_EXECUTOR_MEMORY_MB", "2048"))
DEFAULT_CPU_TIME_LIMIT_SEC = float(os.getenv("AIMO_EXECUTOR_CPU_TIME_SEC", "10.0"))
DEFAULT_CPU_PERCENT_LIMIT = float(os.getenv("AIMO_EXECUTOR_CPU_PERCENT", "100.0"))

FORBIDDEN_BUILTINS = {"open", "exec", "eval", "compile", "__import__"}  # keep safe_import wrapper
FORBIDDEN_MODULES = {"os", "sys", "subprocess", "shutil", "socket", "pathlib", "inspect", "multiprocessing", "threading"}
FORBIDDEN_SUBSTRINGS = [
    "import os", "import sys", "subprocess", "shutil", "socket",
    "multiprocessing", "threading", "__import__", "exec(", "eval(",
    "compile(", "open(", "file(", "__getattr__", "__class__"
]

def _restricted_globals() -> Dict[str, Any]:
    """
    제한된 전역 변수 딕셔너리를 생성합니다.
    
    Returns:
        안전한 전역 변수 딕셔너리
    """
    safe_builtins = {k: v for k, v in builtins.__dict__.items() if k not in FORBIDDEN_BUILTINS}

    # Safe import wrapper: block dangerous modules, allow others.
    def safe_import(name: str, globals=None, locals=None, fromlist=(), level=0):
        """
        안전한 import 래퍼
        
        금지된 모듈의 import를 차단합니다.
        """
        # 모듈 이름에서 점으로 분리된 첫 부분만 체크
        module_name = name.split('.')[0] if '.' in name else name
        
        if module_name in FORBIDDEN_MODULES:
            raise ImportError(f"Blocked import: {module_name}")
        
        # 원래 __import__ 사용 (안전한 모듈만 허용)
        return __import__(name, globals, locals, fromlist, level)

    safe_builtins['__import__'] = safe_import
    g: Dict[str, Any] = {"__builtins__": safe_builtins}
    # 수학 코드 실행에 항상 제공 (생성 코드가 import 누락해도 동작)
    import math
    g["math"] = math
    try:
        import sympy
        g["sympy"] = sympy
    except ImportError:
        pass
    return g

def _run_code(code: str, q: mp.Queue):
    output = StringIO()
    with contextlib.redirect_stdout(output):
        try:
            exec(code, _restricted_globals())
        except Exception as e:
            q.put(f"Error: {e}")
            return
    q.put(output.getvalue())

class CodeExecutor:
    """
    코드 실행기 (고급 리소스 제한 포함)
    
    CPU 시간, 메모리, wall time을 모니터링하고 제한합니다.
    """
    
    def __init__(
        self, 
        timeout_seconds: float = 5.0,
        memory_limit_mb: Optional[int] = None,
        cpu_time_limit_sec: Optional[float] = None,
        cpu_percent_limit: Optional[float] = None
    ):
        """
        Args:
            timeout_seconds: Wall time 타임아웃 (초)
            memory_limit_mb: 메모리 제한 (MB)
            cpu_time_limit_sec: CPU 시간 제한 (초)
            cpu_percent_limit: CPU 사용률 제한 (%)
        """
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb if memory_limit_mb is not None else DEFAULT_MEMORY_LIMIT_MB
        self.cpu_time_limit_sec = cpu_time_limit_sec if cpu_time_limit_sec is not None else DEFAULT_CPU_TIME_LIMIT_SEC
        self.cpu_percent_limit = cpu_percent_limit if cpu_percent_limit is not None else DEFAULT_CPU_PERCENT_LIMIT

    def _basic_static_check(self, code: str) -> Optional[str]:
        """
        코드의 정적 안전성 검사를 수행합니다.
        
        Args:
            code: 검사할 코드
        
        Returns:
            에러 메시지 또는 None (통과)
        """
        code_lower = code.lower()
        
        # 금지된 서브스트링 체크
        for bad in FORBIDDEN_SUBSTRINGS:
            if bad.lower() in code_lower:
                logger.warning(f"Forbidden pattern detected: {bad}")
                return f"Error: Forbidden pattern detected ({bad})"
        
        # AST 문법 검사 (SyntaxError 조기 반환)
        try:
            import ast
            ast.parse(code)
        except SyntaxError as e:
            msg = str(e).split("\n")[0] if e.text is None else f"{e.msg} (line {e.lineno})"
            logger.warning(f"Syntax error in generated code: {msg}")
            return f"Error: Syntax error in code: {msg}"

        return None

    def execute(self, code: str) -> str:
        """
        코드를 실행하고 결과를 반환합니다 (기본 실행).
        
        Args:
            code: 실행할 Python 코드
        
        Returns:
            실행 결과 문자열 또는 에러 메시지
        """
        static_err = self._basic_static_check(code)
        if static_err:
            logger.warning(f"Static check failed: {static_err}")
            return static_err
        
        q: mp.Queue = mp.Queue()
        proc = mp.Process(target=_run_code, args=(code, q))
        start_time = time.time()
        proc.start()
        
        # 실시간 리소스 모니터링
        if psutil:
            try:
                p = psutil.Process(proc.pid)
                while proc.is_alive():
                    elapsed = time.time() - start_time
                    
                    # Wall time 체크
                    if elapsed > self.timeout_seconds:
                        logger.warning(f"Wall time limit exceeded: {elapsed:.2f}s > {self.timeout_seconds}s")
                        self._terminate_process(proc, p)
                        return "Error: Timeout"
                    
                    # CPU 시간 체크
                    try:
                        cpu_times = p.cpu_times()
                        cpu_time = cpu_times.user + cpu_times.system
                        if cpu_time > self.cpu_time_limit_sec:
                            logger.warning(f"CPU time limit exceeded: {cpu_time:.2f}s > {self.cpu_time_limit_sec}s")
                            self._terminate_process(proc, p)
                            return "Error: CPUTimeLimitExceeded"
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                    
                    # 메모리 체크
                    try:
                        mem_mb = p.memory_info().rss / (1024 * 1024)
                        if mem_mb > self.memory_limit_mb:
                            snippet = (code[:400] + "...") if len(code) > 400 else code
                            logger.warning(
                                "Memory limit exceeded: %.2fMB > %dMB (code len=%d). Snippet:\n%s",
                                mem_mb, self.memory_limit_mb, len(code), snippet,
                            )
                            self._terminate_process(proc, p)
                            return "Error: MemoryLimitExceeded"
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                    
                    # CPU 사용률 체크 (과도한 CPU 사용 방지)
                    try:
                        cpu_percent = p.cpu_percent(interval=0.1)
                        if cpu_percent > self.cpu_percent_limit:
                            logger.debug(f"High CPU usage: {cpu_percent:.1f}% (limit: {self.cpu_percent_limit}%)")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                    
                    time.sleep(0.05)  # 모니터링 간격
            except Exception as e:
                logger.debug(f"Resource monitoring error: {e}")
        
        # 기본 타임아웃 체크 (psutil이 없는 경우)
        proc.join(self.timeout_seconds)
        
        if proc.is_alive():
            logger.warning("Process still alive after timeout, terminating...")
            if psutil:
                try:
                    p = psutil.Process(proc.pid)
                    self._terminate_process(proc, p)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    proc.terminate()
                    proc.join()
            else:
                proc.terminate()
                proc.join()
            return "Error: Timeout"
        
        try:
            result = q.get_nowait()
        except Exception as e:
            logger.debug(f"Failed to get result from queue: {e}")
            result = "Error: Unknown execution failure"
        
        return result
    
    def _terminate_process(self, proc: mp.Process, p: Optional[Any] = None) -> None:
        """
        프로세스를 안전하게 종료합니다.
        
        Args:
            proc: 종료할 프로세스
            p: psutil.Process 객체 (선택적)
        """
        try:
            if p and psutil:
                # 자식 프로세스도 함께 종료
                try:
                    children = p.children(recursive=True)
                    for child in children:
                        try:
                            child.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                # 부모 프로세스 종료
                try:
                    p.terminate()
                    p.wait(timeout=1.0)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    try:
                        p.kill()  # 강제 종료
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            else:
                proc.terminate()
                proc.join(timeout=1.0)
                if proc.is_alive():
                    proc.kill()
                    proc.join()
        except Exception as e:
            logger.debug(f"Error terminating process: {e}")

    def execute_with_stats(self, code: str) -> Tuple[str, Dict[str, Any]]:
        """
        코드를 실행하고 리소스 사용 통계와 함께 결과를 반환합니다.
        
        Args:
            code: 실행할 Python 코드
        
        Returns:
            (실행 결과, 리소스 통계 딕셔너리)
        """
        static_err = self._basic_static_check(code)
        if static_err:
            logger.warning(f"Static check failed: {static_err}")
            return static_err, {"error": "static", "wall_ms": 0, "mem_mb": 0, "cpu_ms": 0}
        
        q: mp.Queue = mp.Queue()
        proc = mp.Process(target=_run_code, args=(code, q))
        start = time.time()
        peak_mem = 0.0
        cpu_time_ms = 0.0
        proc.start()
        
        if psutil:
            try:
                p = psutil.Process(proc.pid)
                while True:
                    alive = proc.is_alive()
                    now = time.time()
                    elapsed = now - start
                    
                    if alive:
                        try:
                            # 메모리 모니터링
                            mem_mb = p.memory_info().rss / (1024 * 1024)
                            peak_mem = max(peak_mem, mem_mb)
                            
                            if mem_mb > self.memory_limit_mb:
                                snippet = (code[:400] + "...") if len(code) > 400 else code
                                logger.warning(
                                    "Memory limit exceeded: %.2fMB > %dMB (code len=%d). Snippet:\n%s",
                                    mem_mb, self.memory_limit_mb, len(code), snippet,
                                )
                                self._terminate_process(proc, p)
                                return "Error: MemoryLimitExceeded", {
                                    "wall_ms": elapsed * 1000,
                                    "mem_mb": peak_mem,
                                    "cpu_ms": cpu_time_ms
                                }
                            
                            # CPU 시간 모니터링
                            cpu_times = p.cpu_times()
                            cpu_time = cpu_times.user + cpu_times.system
                            cpu_time_ms = cpu_time * 1000
                            
                            if cpu_time > self.cpu_time_limit_sec:
                                logger.warning(f"CPU time limit exceeded: {cpu_time:.2f}s > {self.cpu_time_limit_sec}s")
                                self._terminate_process(proc, p)
                                return "Error: CPUTimeLimitExceeded", {
                                    "wall_ms": elapsed * 1000,
                                    "mem_mb": peak_mem,
                                    "cpu_ms": cpu_time_ms
                                }
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            break
                    
                    # Wall time 체크
                    if elapsed > self.timeout_seconds:
                        if alive:
                            logger.warning(f"Wall time limit exceeded: {elapsed:.2f}s > {self.timeout_seconds}s")
                            if psutil:
                                try:
                                    self._terminate_process(proc, p)
                                except Exception:
                                    proc.terminate()
                                    proc.join()
                            else:
                                proc.terminate()
                                proc.join()
                        return "Error: Timeout", {
                            "wall_ms": elapsed * 1000,
                            "mem_mb": peak_mem,
                            "cpu_ms": cpu_time_ms
                        }
                    
                    if not alive:
                        break
                    
                    time.sleep(0.01)
            except Exception as e:
                logger.debug(f"Resource monitoring error: {e}")
        else:
            # psutil이 없는 경우 기본 모니터링
            while proc.is_alive():
                elapsed = time.time() - start
                if elapsed > self.timeout_seconds:
                    proc.terminate()
                    proc.join()
                    return "Error: Timeout", {
                        "wall_ms": elapsed * 1000,
                        "mem_mb": 0,
                        "cpu_ms": 0
                    }
                time.sleep(0.01)
        
        # 최종 CPU 시간 측정
        if psutil:
            try:
                p = psutil.Process(proc.pid)
                cpu_times = p.cpu_times()
                cpu_time_ms = (cpu_times.user + cpu_times.system) * 1000
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        try:
            result = q.get_nowait()
        except Exception as e:
            logger.debug(f"Failed to get result from queue: {e}")
            result = "Error: Unknown execution failure"
        
        wall_ms = (time.time() - start) * 1000
        return result, {
            "wall_ms": wall_ms,
            "mem_mb": peak_mem,
            "cpu_ms": cpu_time_ms
        }

if __name__ == "__main__":
    # Example usage (commented out for production)
    # executor = CodeExecutor(timeout_seconds=2)
    # code = """
    # print("Hello from Sandbox")
    # x = 10 + 20
    # print(f"Result: {x}")
    # """
    # print("Normal:", executor.execute(code))
    # infinite = "while True: pass"
    # print("Timeout:", executor.execute(infinite))
    pass
