"""
Model Configuration for AIMO Pipeline
Supports multiple model sizes and quantization options
"""

# Available models (ordered by size)
MODELS = {
    # Small models (development/testing)
    "qwen-0.5b": {
        "name": "Qwen/Qwen2.5-Coder-0.5B-Instruct",
        "description": "Tiny model for fast testing",
        "vram_gb": 2,
        "quantization": None
    },
    
    # Recommended for 8GB VRAM
    "qwen-1.5b": {
        "name": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "description": "Best balance for 8GB GPU (RECOMMENDED)",
        "vram_gb": 4,
        "quantization": None
    },
    
    # Math-specialized models
    "qwen-math-1.5b": {
        "name": "Qwen/Qwen2.5-Math-1.5B-Instruct",
        "description": "Math-specialized 1.5B model",
        "vram_gb": 4,
        "quantization": None
    },
    
    # Large models (require quantization)
    "qwen-7b": {
        "name": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "description": "7B model with 4-bit quantization",
        "vram_gb": 6,
        "quantization": "4bit"
    },
    
    "qwen-math-7b": {
        "name": "Qwen/Qwen2.5-Math-7B-Instruct",
        "description": "Math-specialized 7B with 4-bit quantization",
        "vram_gb": 6,
        "quantization": "4bit"
    },
    
    # Very large (experimental, requires 8-bit or 4-bit)
    "qwen-14b": {
        "name": "Qwen/Qwen2.5-Coder-14B-Instruct",
        "description": "14B model with 4-bit quantization (tight fit)",
        "vram_gb": 8,
        "quantization": "4bit"
    }
}

# Default model selection
import os
DEFAULT_MODEL = os.getenv("OMI_MODEL", "qwen-1.5b")

def get_model_config(model_key=None):
    """Get model configuration"""
    if model_key is None:
        model_key = DEFAULT_MODEL
    
    if model_key not in MODELS:
        print(f"[WARNING] Unknown model: {model_key}, falling back to qwen-1.5b")
        model_key = "qwen-1.5b"
    
    return MODELS[model_key]

def get_quantization_config(quant_type):
    """Get quantization configuration for BitsAndBytes"""
    if quant_type == "4bit":
        try:
            from transformers import BitsAndBytesConfig
            import torch
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        except ImportError:
            print("[WARNING] bitsandbytes not available, skipping quantization")
            return None
    elif quant_type == "8bit":
        try:
            from transformers import BitsAndBytesConfig
            return BitsAndBytesConfig(load_in_8bit=True)
        except ImportError:
            print("[WARNING] bitsandbytes not available, skipping quantization")
            return None
    return None
