"""
평가 설정 파일
경로 및 기본 설정을 중앙에서 관리합니다.
"""

import os
from pathlib import Path

# 프로젝트 루트 디렉터리 (이 파일 기준으로 계산)
EVAL_DIR = Path(__file__).parent
SRC_DIR = EVAL_DIR.parent
PROJECT_ROOT = SRC_DIR.parent

# Kaggle/외부 환경: env로 데이터·결과 경로 override
_AIMO_DATA = os.environ.get("AIMO_DATA_DIR") or os.environ.get("KAGGLE_DATA_DIR")
_AIMO_RESULTS = os.environ.get("AIMO_RESULTS_DIR") or os.environ.get("KAGGLE_WORKING_DIR")

# 데이터 디렉터리 경로 (env 우선, 그 다음 여러 후보)
_DATA_CANDIDATES = [
    PROJECT_ROOT / 'data',
    PROJECT_ROOT / 'AIMO_core' / 'data',
    Path.cwd() / 'data',
    Path.cwd() / 'AIMO_core' / 'data',
]
if _AIMO_DATA:
    DATA_DIRS = [Path(_AIMO_DATA)] + _DATA_CANDIDATES
else:
    DATA_DIRS = _DATA_CANDIDATES.copy()

# 결과 디렉터리 (env 있으면 사용, 없으면 PROJECT_ROOT/results)
RESULTS_DIR = Path(_AIMO_RESULTS) / 'results' if _AIMO_RESULTS else PROJECT_ROOT / 'results'

# 로그 디렉터리
LOGS_DIR = PROJECT_ROOT / 'logs'

def find_data_file(filename: str) -> Path:
    """
    데이터 파일을 여러 위치에서 찾습니다.
    
    Args:
        filename: 찾을 파일 이름
    
    Returns:
        파일 경로
    
    Raises:
        FileNotFoundError: 파일을 찾을 수 없을 때
    """
    candidates = []
    for data_dir in DATA_DIRS:
        candidate = data_dir / filename
        candidates.append(candidate)
        if candidate.exists():
            return candidate
    
    # 에러 메시지에 모든 후보 경로 포함
    error_msg = f"파일을 찾을 수 없습니다: {filename}\n검색한 경로:\n"
    for candidate in candidates:
        error_msg += f"  - {candidate}\n"
    raise FileNotFoundError(error_msg)

def ensure_dir(path: Path) -> Path:
    """
    디렉터리가 존재하는지 확인하고 없으면 생성합니다.
    
    Args:
        path: 디렉터리 경로
    
    Returns:
        생성된/존재하는 디렉터리 경로
    """
    path.mkdir(parents=True, exist_ok=True)
    return path

# 기본 데이터 파일 이름
AIME_VALIDATION_FILE = 'aime_validation_90.json'
NUMINA_EVAL_BALANCED_FILE = 'numina_eval_balanced.json'
NUMINA_TRAINING_FILE = 'numina_training_5k.jsonl'

# 평가 기본 설정
DEFAULT_MAX_PROBLEMS = None  # None이면 전체 평가
DEFAULT_TIME_BUDGET = 60.0  # 초
DEFAULT_USE_SYMPY = True  # SymPy 등가성 검사 사용 여부

# 난이도별 목표 정확도 (%, min–max) — 리포팅/벤치마크 참고용
TARGET_ACCURACY_EASY = (80, 90)    # Easy (Orca)
TARGET_ACCURACY_MEDIUM = (60, 70)  # Medium (K-12)
TARGET_ACCURACY_HARD = (30, 40)    # Hard (Olympiad)
TARGET_ACCURACY_BY_DIFFICULTY = {
    "easy": TARGET_ACCURACY_EASY,
    "medium": TARGET_ACCURACY_MEDIUM,
    "hard": TARGET_ACCURACY_HARD,
}

# Ralph loop default pass/fail floor (overall accuracy unless AIMO_RALPH_GATE_MODE=easy)
RALPH_TARGET_ACCURACY_DEFAULT_PCT = float(TARGET_ACCURACY_EASY[0])
