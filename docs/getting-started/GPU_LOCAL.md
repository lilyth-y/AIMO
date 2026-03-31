# 로컬 NVIDIA GPU (예: RTX 4060 8GB)

- 기본 [`requirements.txt`](../../requirements.txt)의 `torch`는 **CPU 전용** 인덱스입니다. GPU 추론에는 **CUDA용 torch**가 필요합니다.
- 양자화(4bit/8bit)에는 **`bitsandbytes`**가 필요합니다. [`requirements-gpu.txt`](../../requirements-gpu.txt)에 명시되어 있습니다.

## 설치 순서

1. CPU torch 제거 후 PyTorch 공식 안내에 맞는 CUDA 휠 설치: [Get Started](https://pytorch.org/get-started/locally/).
2. `pip install -r requirements-gpu.txt`
3. 확인:

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"
```

## 실행 프로파일

- 모델: 기본 `Qwen/Qwen2.5-Math-7B-Instruct` (`OMI_MODEL` / `AIMO_MODEL`로 변경 가능).
- 양자화: 기본 **4bit** (`AIMO_QUANTIZATION` / `OMI_QUANTIZATION`). 레거시 `MATHCODEORCHESTRATOR_QUANTIZATION`이 있으면 그 값이 우선합니다.
- 스모크: `set MAX_PROBLEMS=2` 후 `python examples/run_numina_evaluation.py`.

Windows에서 `bitsandbytes` 오류가 나면 WSL2 또는 Docker GPU를 검토하세요.
