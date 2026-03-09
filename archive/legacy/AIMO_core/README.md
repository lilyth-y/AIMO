# Moai Project Workspace

This workspace contains the research report and a scaffold implementation of the "5-Stage Deep Reasoning Pipeline" and "Reverse Engineering Data Generation" strategy for the AIMO 3 competition.
The runnable runner and notebook have been rebranded as "Moai" to reflect the local packaging and single-file runner distribution for Kaggle/Colab.

## Directory Structure

- `Report.md`: The full research report detailing the strategy.
- `src/pipeline/`: Python modules implementing the 5 stages of the reasoning pipeline.
    - `stage1_labeling.py`: Problem classification and variable extraction.
    - `stage2_retrieval.py`: Dynamic context loading for domain experts.
    - `stage3_router.py`: The Calculation Router (Simulator vs Theoretician).
    - `stage4_execution.py`: Sandbox execution and error handling.
    - `stage5_verification.py`: Final answer verification and formatting.
- `src/data_generation/`: Modules for synthetic data generation.
    - `reverse_engineering.py`: Algorithms for backward problem generation.

## Getting Started

1.  Read `Report.md` to understand the core philosophy ("Plan & Code").
2.  Explore the `src` directory to see how the architecture is mapped to code.
3.  Run the individual modules to see simple demonstrations of the logic.

```bash
python src/pipeline/stage1_labeling.py
python src/data_generation/reverse_engineering.py
```

## Running strong HF models reliably (Kaggle / Colab)

If you plan to run large models locally or on a Kaggle/Colab runtime, follow these steps:

- Use the `AIMO_core/requirements_kaggle.txt` to install heavy packages (transformers, accelerate, bitsandbytes). On Kaggle/Colab you can run:
    ```bash
    pip install -r AIMO_core/requirements_kaggle.txt
    ```
- Set environment variables to select a model and quantization format. Example:
    ```bash
    export OMI_MODEL=qwen-1.5b
    export OMI_QUANTIZATION=8bit  # or 4bit, or omit for full precision
    ```
    Or on Windows/PowerShell:
    ```powershell
    $env:OMI_MODEL='qwen-1.5b'
    $env:OMI_QUANTIZATION='8bit'
    ```
- When launching the Kaggle runner (`AIMO_core/kaggle_math_pipeline.py`) you can also pass `--model` and `--quant` as CLI arguments which will set the env vars accordingly:
    ```bash
    python AIMO_core/kaggle_math_pipeline.py --model qwen-1.5b --quant 8bit
    ```

Notes:
- `bitsandbytes` requires proper CUDA and driver support; Kaggle/Colab provides GPUs with CUDA support but the exact wheel might depend on CUDA version. In many cases, installing the generic `bitsandbytes` wheel via `pip` suffices.
- Consider setting `OMI_QUANTIZATION` to `8bit` or `4bit` to reduce memory usage. If you set `QUANTIZATION` to `8bit`/`4bit`, the `LocalLLMClient` will attempt to use BitsAndBytesConfig to load quantized models.

Tip: Pre-cache/download model weights to avoid network overhead during runs. You can specify a cache directory and pass it to the runner as `--cache-dir` or set `HF_HOME`/`TRANSFORMERS_CACHE` environment variables:

```bash
export HF_HOME=/kaggle/working/hf_cache
export TRANSFORMERS_CACHE=/kaggle/working/hf_cache
python AIMO_core/kaggle_math_pipeline.py --model qwen-1.5b --quant 8bit --cache-dir /kaggle/working/hf_cache
```

Quick environment check:

```bash
python AIMO_core/check_model_env.py
```
