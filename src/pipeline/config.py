"""Pipeline configuration flags (lightweight).
Adjust here instead of scattering magic numbers.
"""

USE_STRUCTURED = True  # enable structured reasoning prompt
# Keep length threshold as a soft signal (legacy) but move to complexity scoring.
STRUCTURED_LENGTH_THRESHOLD = 120  # legacy length hint (not sole trigger)
COMPLEXITY_STRUCTURED_MIN_SCORE = 5  # min complexity score to trigger structured reasoning
REFINE_PASSES = 0  # future use
LOG_PATH = "logs/eval_log.jsonl"
NUM_CANDIDATES = 3  # multi-candidate generation per strategy
CANDIDATE_TEMPS = [0.2, 0.7, 1.0]
USE_VOTING = False  # disable for initial docker test

# Local HuggingFace model configuration
HF_MODEL_NAME = "C:/Users/USER/.cache/huggingface/hub/models--MathLLMs--MathCoder-L-13B/snapshots/467c30837267f1ca4554d93652ec35392ea7aa1d"  # MathCoder model for mathematical reasoning (local HF cache)
QUANTIZATION_DEFAULT = "8bit"  # Reduced from 4bit for better stability
DECOMPOSITION_COMPLEXITY_THRESHOLD = 15  # Complexity score threshold for decomposition
