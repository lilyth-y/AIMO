"""
NuminaMath Dataset Loader and Integration
- NuminaMath-1.5: 896k high-quality math problems with Chain-of-Thought solutions
- NuminaMath-CoT: 860k problems (previous version)
- aimo-validation-aime: 90 official AIME problems (2022-2024)
- Sources: Chinese K12, Olympiads, AMC/AIME, GSM8K, etc.
- Used by AIMO Prize winners for training
"""

from datasets import load_dataset
import json
import random
from typing import List, Dict, Any, Optional
import os

class NuminaMathDataLoader:
    """
    Loads and manages NuminaMath datasets for training/evaluation
    Supports:
    - NuminaMath-1.5 (896k, with metadata: answer, problem_type, question_type)
    - NuminaMath-CoT (860k, original version)
    - aimo-validation-aime (90 official AIME 2022-2024)
    """
    def __init__(self, cache_dir: str = "./data/numina_cache", version: str = "1.5"):
        self.cache_dir = cache_dir
        self.version = version  # "1.5" or "CoT"
        self.dataset = None
        self.aime_dataset = None
        
        # NuminaMath-1.5 source breakdown (896k total)
        self.sources_v15 = {
            'olympiads': 197084,
            'olympiads_ref': 3638,  # NEW: Manually curated
            'cn_k12': 268819,
            'aops_forum': 67841,
            'cn_contest': 29944,  # NEW: Contest problems
            'orca_math': 151934,
            'synthetic_math': 148712,
            'amc_aime': 5872,
            'inequalities': 7314,  # NEW: Inequalities
            'number_theory': 4043,  # NEW: Number theory
            'metamath': 11014
        }
        
        # NuminaMath-CoT source breakdown (860k total) - legacy
        self.sources_cot = {
            'aops_forum': 30201,
            'amc_aime': 4072,
            'cn_k12': 276591,
            'gsm8k': 7345,
            'math': 7478,
            'olympiads': 150581,
            'orca_math': 153334,
            'synthetic_amc': 62111,
            'synthetic_math': 167895
        }
        
        self.sources = self.sources_v15 if version == "1.5" else self.sources_cot
    
    def load_dataset(self, split: str = 'train', streaming: bool = False):
        """
        Load NuminaMath dataset from Hugging Face
        
        Args:
            split: Dataset split ('train' only available)
            streaming: Whether to stream the dataset (recommended for large datasets)
        """
        dataset_name = "AI-MO/NuminaMath-1.5" if self.version == "1.5" else "AI-MO/NuminaMath-CoT"
        total_samples = "896k" if self.version == "1.5" else "860k"
        
        print(f"Loading {dataset_name} (split={split}, streaming={streaming})...")
        
        self.dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming,
            cache_dir=self.cache_dir
        )
        
        print(f"✅ Dataset loaded! Total samples: ~{total_samples}")
        if self.version == "1.5":
            print("   Includes metadata: answer, problem_type, question_type")
        return self.dataset
    
    def load_aime_validation(self, split: str = 'train'):
        """
        Load AIMO Validation AIME dataset (90 official AIME 2022-2024 problems)
        
        Args:
            split: Dataset split ('train' only available)
        """
        print(f"Loading AIMO Validation AIME dataset (split={split})...")
        
        self.aime_dataset = load_dataset(
            "AI-MO/aimo-validation-aime",
            split=split,
            cache_dir=self.cache_dir
        )
        
        print(f"✅ AIME validation set loaded! Total samples: {len(self.aime_dataset)}")
        print("   Source: AIME 2022, 2023, 2024 (official benchmark)")
        return self.aime_dataset
    
    def get_sample_by_source(self, source: str, n: int = 10) -> List[Dict]:
        """
        Get n random samples from a specific source
        
        Args:
            source: One of the source names (e.g., 'olympiads', 'amc_aime')
            n: Number of samples to retrieve
        """
        if self.dataset is None:
            self.load_dataset(streaming=True)
        
        samples = []
        for item in self.dataset:
            if item['source'] == source:
                samples.append(item)
                if len(samples) >= n:
                    break
        
        return samples
    
    def get_difficulty_samples(self, difficulty: str, n: int = 10) -> List[Dict]:
        """
        Get samples by difficulty level
        
        Args:
            difficulty: 'easy' (orca_math, gsm8k), 
                       'medium' (cn_k12, synthetic_math),
                       'hard' (olympiads, amc_aime, aops_forum)
            n: Number of samples
        """
        difficulty_mapping = {
            'easy': ['orca_math', 'gsm8k'],
            'medium': ['cn_k12', 'synthetic_math', 'synthetic_amc'],
            'hard': ['olympiads', 'amc_aime', 'aops_forum', 'math']
        }
        
        sources = difficulty_mapping.get(difficulty, [])
        if not sources:
            raise ValueError(f"Unknown difficulty: {difficulty}")
        
        if self.dataset is None:
            self.load_dataset(streaming=True)
        
        samples = []
        for item in self.dataset:
            if item['source'] in sources:
                samples.append(item)
                if len(samples) >= n:
                    break
        
        return samples
    
    def create_evaluation_set(self, 
                             n_easy: int = 20,
                             n_medium: int = 30,
                             n_hard: int = 50,
                             output_file: str = "numina_eval_set.json"):
        """
        Create a balanced evaluation set
        
        Args:
            n_easy, n_medium, n_hard: Number of samples per difficulty
            output_file: Output JSON file
        """
        print("Creating evaluation set from NuminaMath-CoT...")
        
        eval_set = []
        
        # Get samples by difficulty
        easy = self.get_difficulty_samples('easy', n_easy)
        medium = self.get_difficulty_samples('medium', n_medium)
        hard = self.get_difficulty_samples('hard', n_hard)
        
        eval_set.extend(easy)
        eval_set.extend(medium)
        eval_set.extend(hard)
        
        # Shuffle
        random.shuffle(eval_set)
        
        # Save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(eval_set, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Evaluation set created: {len(eval_set)} problems")
        print(f"   Easy: {len(easy)}, Medium: {len(medium)}, Hard: {len(hard)}")
        print(f"   Saved to: {output_file}")
        
        return eval_set
    
    def format_for_training(self, sample: Dict) -> Dict[str, str]:
        """
        Format a sample for training (similar to our current format)
        
        Returns:
            {
                "problem": str,
                "solution": str (CoT format),
                "answer": str (extracted final answer),
                "source": str,
                "problem_type": str (v1.5 only),
                "question_type": str (v1.5 only)
            }
        """
        import re
        
        problem = sample['problem']
        solution = sample['solution']
        
        # For v1.5, use provided answer metadata
        if self.version == "1.5" and 'answer' in sample:
            answer = sample['answer']
        else:
            # Extract final answer (usually in \boxed{} format)
            boxed_match = re.search(r'\\boxed\{([^}]+)\}', solution)
            if boxed_match:
                answer = boxed_match.group(1)
            else:
                # Fallback: last number or expression
                answer = "See solution"
        
        result = {
            "problem": problem,
            "solution": solution,
            "answer": answer,
            "source": sample['source']
        }
        
        # Add v1.5 metadata if available
        if self.version == "1.5":
            if 'problem_type' in sample:
                result['problem_type'] = sample['problem_type']
            if 'question_type' in sample:
                result['question_type'] = sample['question_type']
        
        return result
    
    def format_aime_problem(self, sample: Dict) -> Dict[str, str]:
        """
        Format an AIME validation problem
        
        Returns:
            {
                "problem": str,
                "solution": str,
                "url": str (source link)
            }
        """
        return {
            "problem": sample['problem'],
            "solution": sample['solution'],
            "url": sample.get('url', '')
        }
    
    def export_training_data(self, 
                            n_samples: int = 10000,
                            output_file: str = "numina_training_data.jsonl"):
        """
        Export formatted training data
        
        Args:
            n_samples: Number of samples to export
            output_file: Output JSONL file (line-delimited JSON)
        """
        if self.dataset is None:
            self.load_dataset(streaming=True)
        
        print(f"Exporting {n_samples} training samples...")
        
        count = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in self.dataset:
                formatted = self.format_for_training(item)
                f.write(json.dumps(formatted, ensure_ascii=False) + '\n')
                count += 1
                
                if count >= n_samples:
                    break
                
                if count % 1000 == 0:
                    print(f"   Processed: {count}/{n_samples}")
        
        print(f"✅ Training data exported: {output_file}")
        return output_file
    
    def analyze_dataset(self):
        """
        Analyze dataset statistics
        """
        version_str = "NuminaMath-1.5" if self.version == "1.5" else "NuminaMath-CoT"
        total_samples = "896,000" if self.version == "1.5" else "860,000"
        
        print(f"\n=== {version_str} Dataset Analysis ===")
        print(f"Total samples: ~{total_samples}")
        print("\nSource breakdown:")
        
        total = sum(self.sources.values())
        for source, count in sorted(self.sources.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            marker = "" if self.version == "CoT" else " [NEW]" if source in ['olympiads_ref', 'cn_contest', 'inequalities', 'number_theory'] else ""
            print(f"  {source:20s}: {count:7d} ({percentage:5.2f}%){marker}")
        
        if self.version == "1.5":
            print("\nMetadata fields:")
            print("  - answer: Final answer (number/proof/notfound)")
            print("  - problem_type: Domain (Algebra, Geometry, Number Theory, etc.)")
            print("  - question_type: MCQ, proof, or math-word-problem")
        
        print("\nDifficulty distribution (estimated):")
        if self.version == "1.5":
            print(f"  Easy   (Orca): ~152k (17.0%)")
            print(f"  Medium (CN_K12, Synthetic, MetaMath): ~428k (47.8%)")
            print(f"  Hard   (Olympiads, AMC, AOPS, Contests): ~316k (35.2%)")
        else:
            print(f"  Easy   (GSM8K, Orca): ~160k (18.6%)")
            print(f"  Medium (CN_K12, Synthetic): ~506k (58.9%)")
            print(f"  Hard   (Olympiads, AMC, AOPS): ~193k (22.5%)")
        
        print("\nKey features:")
        print("  - All solutions in Chain-of-Thought (CoT) format")
        print("  - English translations")
        print("  - Final answers in \\boxed{} format")
        print("  - Covers: Algebra, Geometry, Number Theory, Combinatorics, etc.")
        
        if self.version == "1.5":
            print("\nImprovements in v1.5:")
            print("  - +36k problems (896k vs 860k)")
            print("  - Manual curation of Olympiad problems (olympiads_ref)")
            print("  - New contest, inequalities, number theory data")
            print("  - Rich metadata for filtering and analysis")
            print("  - Removed low-quality synthetic data")
        
        print("\nUsage in AIMO winners:")
        print("  - NuminaMath team: Fine-tuned DeepSeek models on this data")
        print("  - Tool-Integrated Reasoning (TIR) framework")
        print("  - Achieved 29/50 on AIMO Progress Prize")


def create_aimo_evaluation_suite(version: str = "1.5", include_aime: bool = True):
    """
    Create a comprehensive evaluation suite
    
    Args:
        version: "1.5" (recommended, 896k with metadata) or "CoT" (860k, legacy)
        include_aime: Whether to include AIME validation set (90 official problems)
    """
    loader = NuminaMathDataLoader(version=version)
    
    # Analysis
    loader.analyze_dataset()
    
    # Load AIME validation set
    aime_set = None
    if include_aime:
        print("\n" + "="*60)
        aime_dataset = loader.load_aime_validation()
        aime_set = [loader.format_aime_problem(item) for item in aime_dataset]
        
        # Save AIME set
        aime_file = "data/aime_validation_90.json"
        with open(aime_file, 'w', encoding='utf-8') as f:
            json.dump(aime_set, f, indent=2, ensure_ascii=False)
        print(f"✅ AIME validation set saved: {aime_file}")
    
    # Create evaluation set from main dataset
    print("\n" + "="*60)
    eval_set = loader.create_evaluation_set(
        n_easy=10,
        n_medium=20,
        n_hard=30,
        output_file="data/numina_eval_balanced.json"
    )
    
    # Export some training data for fine-tuning
    print("\n" + "="*60)
    loader.export_training_data(
        n_samples=5000,
        output_file="data/numina_training_5k.jsonl"
    )
    
    return loader, eval_set, aime_set


if __name__ == "__main__":
    # Create comprehensive evaluation suite with NuminaMath-1.5 and AIME
    loader, eval_set, aime_set = create_aimo_evaluation_suite(
        version="1.5",  # Use latest version
        include_aime=True  # Include official AIME benchmark
    )
    
    # Show sample from NuminaMath
    print("\n" + "="*60)
    print("Sample problem from NuminaMath-1.5:")
    print("="*60)
    
    if eval_set:
        sample = eval_set[0]
        print(f"\nSource: {sample['source']}")
        if 'problem_type' in sample:
            print(f"Type: {sample['problem_type']} | Question: {sample['question_type']}")
        print(f"\nProblem:\n{sample['problem'][:300]}...")
        print(f"\nSolution (first 500 chars):\n{sample['solution'][:500]}...")
    
    # Show sample from AIME
    if aime_set:
        print("\n" + "="*60)
        print("Sample problem from AIME Validation:")
        print("="*60)
        sample = aime_set[0]
        print(f"\nProblem:\n{sample['problem'][:300]}...")
        print(f"\nURL: {sample['url']}")
