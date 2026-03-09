
# Diagnostic script: check MATHCODEORCHESTRATOR_MODEL env and attempt to load HF pipeline
import os, traceback, sys

model = os.getenv('MATHCODEORCHESTRATOR_MODEL', 'models--Qwen--Qwen2.5-Math-72B-Instruct').strip()
quant = os.getenv('MATHCODEORCHESTRATOR_QUANTIZATION', None)
print('MATHCODEORCHESTRATOR_MODEL:', model)
print('MATHCODEORCHESTRATOR_QUANTIZATION:', quant)
print('Python executable:', sys.executable)

try:
    from transformers import pipeline
    import torch
    kwargs = {}
    # device map
    if torch.cuda.is_available():
        kwargs['device_map'] = 'auto'
        print('CUDA available: using device_map=auto')
    else:
        # On CPU-only environments avoid device_map to prevent errors
        print('CUDA not available: attempting CPU load (may fail for very large models)')

    if quant == '8bit':
        kwargs['load_in_8bit'] = True
    elif quant == '4bit':
        kwargs['load_in_4bit'] = True

    print('Attempting to create text-generation pipeline with kwargs:', kwargs)
    p = pipeline('text-generation', model=model, **kwargs)
    print('SUCCESS: pipeline created. Example generation (truncated):')
    out = p('Hello', max_new_tokens=16, do_sample=False, num_return_sequences=1)
    print(out[0])
except Exception:
    print('FAILED to load model/pipeline — full traceback below:')
    traceback.print_exc()
    print('\nHints:')
    print('- Ensure the path exists and is the exact folder name for the model.')
    print("- If the model is local (GGUF), transformers may not support it directly; use appropriate loader or convert.")
    print("- Set HF cache via HF_HOME/TRANSFORMERS_CACHE if model files are in a custom dir.")
    print("- For repo models requiring custom code, try passing trust_remote_code=True in pipeline kwargs.")
