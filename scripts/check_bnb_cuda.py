import bitsandbytes as bnb
import torch
import sys
print('bitsandbytes:', bnb.__version__)
print('torch:', torch.__version__)
print('cuda_available:', torch.cuda.is_available())
print('cuda_count:', torch.cuda.device_count())
if torch.cuda.is_available():
    print('cuda_device:', torch.cuda.get_device_name(0))
sys.stdout.flush()