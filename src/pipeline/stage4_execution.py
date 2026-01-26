"""Stage 4: Execution & Error Correction
개선:
 - 멀티프로세스 기반 타임아웃 (Windows 호환)
 - 기본 stdout 캡처
 - 간단한 안전 필터 (위험한 내장 / 파일 I/O 차단)
주의: 완전한 샌드박스 아님 (프로덕션에서는 별도 격리 필요)
"""

from io import StringIO
import multiprocessing as mp
import contextlib
import builtins
import time
import os
try:
    import psutil  # optional for resource stats
except ImportError:
    psutil = None

DEFAULT_MEMORY_LIMIT_MB = int(os.getenv("AIMO_EXECUTOR_MEMORY_MB", "768"))

FORBIDDEN_BUILTINS = {"open", "exec", "eval", "compile"}  # keep __import__ for normal import semantics
FORBIDDEN_MODULES = {"os", "sys", "subprocess", "shutil", "socket", "pathlib", "inspect"}
FORBIDDEN_SUBSTRINGS = ["import os", "import sys", "subprocess", "shutil", "socket"]

def _restricted_globals():
    safe_builtins = {k: v for k, v in builtins.__dict__.items() if k not in FORBIDDEN_BUILTINS}

    # Safe import wrapper: block dangerous modules, allow others.
    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in FORBIDDEN_MODULES:
            raise ImportError(f"Blocked import: {name}")
        return __import__(name, globals, locals, fromlist, level)

    safe_builtins['__import__'] = safe_import
    return {"__builtins__": safe_builtins}

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
    def __init__(self, timeout_seconds=5, memory_limit_mb: int | None = None):
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb if memory_limit_mb is not None else DEFAULT_MEMORY_LIMIT_MB

    def _basic_static_check(self, code: str) -> str | None:
        for bad in FORBIDDEN_SUBSTRINGS:
            if bad in code:
                return f"Error: Forbidden pattern detected ({bad})"
        return None

    def execute(self, code: str) -> str:
        static_err = self._basic_static_check(code)
        if static_err:
            return static_err
        q: mp.Queue = mp.Queue()
        proc = mp.Process(target=_run_code, args=(code, q))
        start_time = time.time()
        proc.start()
        proc.join(self.timeout_seconds)
        # simple memory check after join
        if psutil and proc.is_alive():
            try:
                mem_mb = psutil.Process(proc.pid).memory_info().rss / (1024*1024)
                if mem_mb > self.memory_limit_mb:
                    proc.terminate(); proc.join()
                    return "Error: MemoryLimitExceeded"
            except Exception:
                pass
        if proc.is_alive():
            proc.terminate(); proc.join()
            return "Error: Timeout"
        try:
            result = q.get_nowait()
        except Exception:
            result = "Error: Unknown execution failure"
        return result

    def execute_with_stats(self, code: str):
        static_err = self._basic_static_check(code)
        if static_err:
            return static_err, {"error": "static"}
        q: mp.Queue = mp.Queue()
        proc = mp.Process(target=_run_code, args=(code, q))
        start = time.time()
        peak_mem = 0.0
        proc.start()
        while True:
            alive = proc.is_alive()
            now = time.time()
            if psutil and alive:
                try:
                    mem_mb = psutil.Process(proc.pid).memory_info().rss / (1024*1024)
                    peak_mem = max(peak_mem, mem_mb)
                    if mem_mb > self.memory_limit_mb:
                        proc.terminate(); proc.join()
                        return "Error: MemoryLimitExceeded", {"wall_ms": (now-start)*1000, "mem_mb": peak_mem, "cpu_ms": None}
                except Exception:
                    pass
            if (now - start) > self.timeout_seconds:
                if alive:
                    proc.terminate(); proc.join()
                return "Error: Timeout", {"wall_ms": (now-start)*1000, "mem_mb": peak_mem, "cpu_ms": None}
            if not alive:
                break
            time.sleep(0.01)
        try:
            result = q.get_nowait()
        except Exception:
            result = "Error: Unknown execution failure"
        wall_ms = (time.time() - start)*1000
        return result, {"wall_ms": wall_ms, "mem_mb": peak_mem, "cpu_ms": None}

if __name__ == "__main__":
    executor = CodeExecutor(timeout_seconds=2)
    code = """
print("Hello from Sandbox")
x = 10 + 20
print(f"Result: {x}")
"""
    print("Normal:", executor.execute(code))
    infinite = "while True: pass"
    print("Timeout:", executor.execute(infinite))
