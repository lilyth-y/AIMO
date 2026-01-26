"""
Quick environment check for heavy model runs.
This script prints the model/quantization env vars, checks for torch/cuda, bitsandbytes availability,
and exits with non-zero status if critical pieces are missing.
"""
import os
import sys
print('AIMO_MODEL:', os.environ.get('AIMO_MODEL'))
print('AIMO_QUANTIZATION:', os.environ.get('AIMO_QUANTIZATION'))
try:
    import torch
    print('Torch: ', torch.__version__)
    print('CUDA available: ', torch.cuda.is_available())
    if torch.cuda.is_available():
        print('CUDA device name:', torch.cuda.get_device_name(0))
except Exception as e:
    print('Torch import error:', e)
try:
    import bitsandbytes as bnb
    print('bitsandbytes:', getattr(bnb, '__version__', 'unknown'))
except Exception as e:
    print('bitsandbytes: not available (or import error)', e)
try:
    import accelerate
    print('accelerate module present')
except Exception as e:
    print('accelerate: not available', e)

print('Installation checks complete')

if __name__ == '__main__':
    # exit nonzero if torch not present
    try:
        import torch
        if not torch.cuda.is_available():
            print('WARNING: cuda not available; quantized multi-gpu loading may fail')
    except Exception:
        print('ERROR: torch not present. Install via requirements_kaggle.txt or pip install torch')
        sys.exit(2)
    sys.exit(0)
