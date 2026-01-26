# NuminaMath-1.5 + AIME Validation Integration

## Overview

This document describes the upgrade to **NuminaMath-1.5** (896k problems) and integration of **aimo-validation-aime** (90 official AIME problems) for comprehensive evaluation.

## What's New

### NuminaMath-1.5 (896k problems)

**Compared to NuminaMath-CoT (860k):**

#### 1. **More Data (+36k problems)**
- **896,215 total problems** (vs 860k in CoT)
- Better coverage of advanced topics

#### 2. **Rich Metadata**
Every problem now includes:

```python
{
    "problem": "...",
    "solution": "...",
    "source": "olympiads",
    "answer": "42",              # NEW: Final answer (number/proof/notfound)
    "problem_type": "Geometry",  # NEW: Domain classification
    "question_type": "math-word-problem"  # NEW: Problem format
}
```

**Problem Types:**
- Algebra
- Geometry
- Number Theory
- Combinatorics
- Calculus
- Inequalities
- Logic and Puzzles
- Other

**Question Types:**
- `math-word-problem`: Standard problem with numerical answer
- `proof`: Proof-based problems
- `multiple-choice`: MCQ format

#### 3. **Improved Data Quality**

**New Sources:**
- `olympiads_ref` (3,638): **Manually curated** from official Olympiad websites
  - Fixes parsing errors in original `olympiads` subset
  - Direct extraction from official PDFs
  
- `cn_contest` (29,944): High-quality Chinese math competition problems

- `inequalities` (7,314): Specialized inequality problems

- `number_theory` (4,043): Dedicated number theory problems

**Removed:**
- `synthetic_amc` (62,111): Removed due to performance degradation in ablation studies

**Updated:**
- `olympiads` (197,084): Expanded coverage
- `aops_forum` (67,841): More problems from Art of Problem Solving

### AIME Validation Set (90 problems)

**Dataset:** `AI-MO/aimo-validation-aime`

**Source:** Official AIME competitions
- AIME 2022
- AIME 2023  
- AIME 2024

**Purpose:** Standardized benchmark for AIME-level performance

**Structure:**
```python
{
    "problem": "...",
    "solution": "... \\boxed{answer} ...",
    "url": "https://artofproblemsolving.com/wiki/..."
}
```

**Why AIME?**
- Official competition problems
- Well-defined difficulty level
- Public solutions available
- Standard benchmark in math AI research

## Source Breakdown

### NuminaMath-1.5 (896,215 total)

| Source | Count | Percentage | Type |
|--------|-------|------------|------|
| cn_k12 | 268,819 | 30.0% | Chinese K-12 curriculum |
| olympiads | 197,084 | 22.0% | Math Olympiads |
| orca_math | 151,934 | 17.0% | Easy word problems |
| synthetic_math | 148,712 | 16.6% | Synthetic problems |
| aops_forum | 67,841 | 7.6% | Art of Problem Solving |
| cn_contest | 29,944 | 3.3% | **[NEW]** Contest problems |
| metamath | 11,014 | 1.2% | MetaMath dataset |
| inequalities | 7,314 | 0.8% | **[NEW]** Inequalities |
| amc_aime | 5,872 | 0.7% | AMC/AIME problems |
| number_theory | 4,043 | 0.5% | **[NEW]** Number theory |
| olympiads_ref | 3,638 | 0.4% | **[NEW]** Curated Olympiads |

**Difficulty Distribution:**
- **Easy** (Orca): ~152k (17.0%)
- **Medium** (CN_K12, Synthetic, MetaMath): ~428k (47.8%)
- **Hard** (Olympiads, AMC, AOPS, Contests): ~316k (35.2%)

## Integration Guide

### 1. Setup

```bash
# Install dependencies
pip install datasets transformers

# Download datasets (first time only, ~2GB)
python setup_numina_dataset.py
```

**Output:**
- `data/aime_validation_90.json` - AIME validation set
- `data/numina_eval_balanced.json` - Balanced NuminaMath eval
- `data/numina_training_5k.jsonl` - Training samples
- `data/numina_cache/` - Cached datasets

### 2. Using the Loader

```python
from data.numina_loader import NuminaMathDataLoader

# Initialize with v1.5
loader = NuminaMathDataLoader(version="1.5")

# Load main dataset (streaming recommended)
dataset = loader.load_dataset(streaming=True)

# Load AIME validation
aime = loader.load_aime_validation()

# Access metadata (v1.5 only)
for sample in dataset:
    print(f"Type: {sample['problem_type']}")
    print(f"Question: {sample['question_type']}")
    print(f"Answer: {sample['answer']}")
    break
```

### 3. Evaluation Strategy

**Two-Tier Evaluation:**

#### Tier 1: AIME Validation (Official Benchmark)
```bash
python run_aime_evaluation.py
```

**Purpose:**
- Standardized AIME-level benchmark
- Comparable to published results
- 90 high-quality problems

**Expected Performance:**
- GPT-4: ~45%
- AIMO Winners: ~58% (29/50 on AIMO Prize)
- Your baseline: TBD

#### Tier 2: NuminaMath Balanced (Development)
```bash
python run_numina_evaluation.py
```

**Purpose:**
- Mixed difficulty testing
- 60 problems (10 easy, 20 medium, 30 hard)
- Broader coverage

### 4. Filtering by Metadata (v1.5)

```python
# Filter by problem type
geometry_problems = [
    sample for sample in dataset 
    if sample['problem_type'] == 'Geometry'
]

# Filter by question type
proofs = [
    sample for sample in dataset
    if sample['question_type'] == 'proof'
]

# Get problems with numerical answers
solvable = [
    sample for sample in dataset
    if sample['answer'] not in ['proof', 'notfound']
]
```

## Comparison: CoT vs 1.5

| Feature | NuminaMath-CoT | NuminaMath-1.5 |
|---------|----------------|----------------|
| **Size** | 860k | 896k (+36k) |
| **Metadata** | Basic (source only) | Rich (answer, types) |
| **Data Quality** | Good | Better (manual curation) |
| **Olympiads** | Auto-parsed (errors) | Manual + auto |
| **Filtering** | By source only | By type, difficulty, format |
| **Answer Extraction** | Regex only | Pre-extracted + regex |
| **New Domains** | No | Inequalities, Number Theory |
| **Recommended** | Legacy | ✅ **Yes** |

## Migration from CoT to 1.5

**Code Changes Required:**

1. **Loader initialization:**
```python
# Before
loader = NuminaMathDataLoader()

# After
loader = NuminaMathDataLoader(version="1.5")
```

2. **Access new metadata:**
```python
# Now available
sample['answer']        # Pre-extracted answer
sample['problem_type']  # Domain classification
sample['question_type'] # Problem format
```

3. **Updated source names:**
- New: `olympiads_ref`, `cn_contest`, `inequalities`, `number_theory`
- Removed: `synthetic_amc`, `gsm8k`
- Expanded: `olympiads`, `aops_forum`

**Backward Compatibility:**
- All CoT code still works with v1.5
- Just pass `version="CoT"` if needed
- New features are optional

## Evaluation Workflow

```
1. Setup
   └─> python setup_numina_dataset.py
       ├─> Downloads NuminaMath-1.5 (896k)
       ├─> Downloads AIME validation (90)
       ├─> Creates eval sets
       └─> Exports training samples

2. AIME Benchmark (Official)
   └─> python run_aime_evaluation.py
       ├─> 90 AIME problems (2022-2024)
       ├─> Exact answer matching
       └─> Compare with published results

3. NuminaMath Eval (Development)
   └─> python run_numina_evaluation.py
       ├─> 60 balanced problems
       ├─> Mixed difficulty
       └─> Broader coverage testing

4. System Comparison
   └─> Compare: Standard TIR vs Hierarchical vs Hybrid
       ├─> On AIME validation
       ├─> On NuminaMath balanced
       └─> Identify strengths/weaknesses
```

## Benefits of Upgrade

### 1. **Better Training Data**
- +36k more problems
- Higher quality (manual curation)
- Better domain coverage

### 2. **Rich Metadata**
- Filter by problem type
- Select by difficulty
- Analyze performance by domain

### 3. **Official Benchmark**
- AIME validation set
- Standardized comparison
- Publishable results

### 4. **Improved Evaluation**
- Two-tier testing
- Type-specific analysis
- Better error diagnosis

### 5. **Future-Proof**
- Latest dataset version
- Active maintenance
- Community support

## Performance Expectations

### AIME Validation (90 problems)

**Difficulty:** AIME competition level

**Baselines:**
- Random guessing: ~0.4% (1/250)
- GPT-4: ~45%
- AIMO Winners: ~58%
- Human AIME average: ~5-6 correct (33-40%)

**Your System Goals:**
- **Baseline (current):** TBD
- **Target:** 50%+ (competitive)
- **Stretch:** 60%+ (SOTA for open models)

### NuminaMath Balanced (60 problems)

**Mix:**
- 10 easy (Orca-level)
- 20 medium (K-12 level)
- 30 hard (Olympiad-level)

**Expected:**
- Easy: 80-90%
- Medium: 60-70%
- Hard: 30-40%
- **Overall: 55-65%**

## Troubleshooting

### Dataset Download Fails
```bash
# Check internet connection
# Retry with cache clear
rm -rf data/numina_cache
python setup_numina_dataset.py
```

### Memory Issues
```python
# Use streaming mode
dataset = loader.load_dataset(streaming=True)
```

### Slow Loading
```python
# Datasets cached after first load
# Location: data/numina_cache/
# Subsequent loads are fast
```

## References

1. **NuminaMath-1.5:**
   - https://huggingface.co/datasets/AI-MO/NuminaMath-1.5
   - 896k problems, Apache 2.0 license
   - Published: February 2024

2. **AIME Validation:**
   - https://huggingface.co/datasets/AI-MO/aimo-validation-aime
   - 90 AIME 2022-2024 problems
   - Source: Art of Problem Solving wiki

3. **AIMO Progress Prize:**
   - https://github.com/project-numina/aimo-progress-prize
   - Winners' solution used this data
   - Achieved 29/50 (58%)

## Next Steps

1. ✅ **Setup datasets** - `python setup_numina_dataset.py`
2. ⏳ **Run AIME benchmark** - `python run_aime_evaluation.py`
3. ⏳ **Run NuminaMath eval** - `python run_numina_evaluation.py`
4. ⏳ **Compare systems** - Standard vs Hierarchical vs Hybrid
5. ⏳ **Analyze results** - Identify improvement areas
6. ⏳ **Fine-tune** (optional) - On training data
7. ⏳ **Iterate** - Improve based on results
