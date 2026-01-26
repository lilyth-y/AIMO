"""
Setup NuminaMath Dataset for AIMO Project
- NuminaMath-1.5: 896k problems with rich metadata
- aimo-validation-aime: 90 official AIME problems
- Creates evaluation sets
- Exports training data samples
"""

import sys
sys.path.append('src')

from data.numina_loader import NuminaMathDataLoader, create_aimo_evaluation_suite

def main():
    print("="*70)
    print("NuminaMath-1.5 + AIME Dataset Setup for AIMO Project")
    print("="*70)
    print("\nThis will:")
    print("1. Download NuminaMath-1.5 dataset (~896k problems)")
    print("2. Download AIME validation set (90 official AIME 2022-2024)")
    print("3. Create balanced evaluation set (60 problems)")
    print("4. Export 5000 training samples")
    print("\nImprovements in v1.5:")
    print("  - +36k more problems (896k vs 860k)")
    print("  - Metadata: answer, problem_type, question_type")
    print("  - Manually curated Olympiad problems")
    print("  - New contest/inequalities/number theory data")
    print("\nNote: First download may take time. Data will be cached locally.")
    print("="*70)
    
    # Run the setup with v1.5 and AIME
    loader, eval_set, aime_set = create_aimo_evaluation_suite(
        version="1.5",
        include_aime=True
    )
    
    print("\n" + "="*70)
    print("✅ Setup Complete!")
    print("="*70)
    print("\nGenerated files:")
    print("  - data/aime_validation_90.json (90 AIME problems - official benchmark)")
    print("  - data/numina_eval_balanced.json (60 problems for evaluation)")
    print("  - data/numina_training_5k.jsonl (5000 samples for fine-tuning)")
    print("\nDataset cache:")
    print("  - ./data/numina_cache/ (for faster future loading)")
    print("\nRecommended evaluation strategy:")
    print("  1. Benchmark on AIME validation (90 problems, AIME-level)")
    print("  2. Test on balanced NuminaMath set (60 problems, mixed difficulty)")
    print("  3. Compare: Standard TIR vs Hierarchical vs Hybrid systems")
    print("\nNext steps:")
    print("  1. Run AIME benchmark: python run_aime_evaluation.py")
    print("  2. Run NuminaMath eval: python run_numina_evaluation.py")
    print("  3. Fine-tune model on training data (optional)")
    print("="*70)

if __name__ == "__main__":
    main()
