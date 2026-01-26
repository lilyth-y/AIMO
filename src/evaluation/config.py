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

# 데이터 디렉터리 경로 (여러 후보 위치 확인)
DATA_DIRS = [
    PROJECT_ROOT / 'data',
    PROJECT_ROOT / 'AIMO_core' / 'data',
    Path.cwd() / 'data',
    Path.cwd() / 'AIMO_core' / 'data',
]

# 결과 디렉터리
RESULTS_DIR = PROJECT_ROOT / 'results'

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
