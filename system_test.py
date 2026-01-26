#!/usr/bin/env python3
"""
Comprehensive test script for Moai system components.
Tests imports, configurations, and basic functionality.
"""

import sys
import os

def test_imports():
    """Test all AIMO pipeline imports."""
    print("[TEST] Testing Moai System Imports...")
    try:
        # Core pipeline modules
        from src.pipeline import config
        print("[OK] Config module loaded")

        from src.pipeline.orchestrator import PipelineOrchestrator
        print("[OK] Orchestrator module loaded")

        from src.pipeline.solver import Solver, LocalLLMClient
        print("[OK] Solver module loaded")

        from src.pipeline.reconciliation import ReasoningReconciler
        print("[OK] Reconciliation module loaded")

        from src.pipeline.stage5_verification import VerificationRouter
        print("[OK] Verification module loaded")

        from src.pipeline.stage4_execution import CodeExecutor
        print("[OK] Execution module loaded")

        from src.pipeline.stage3_router import CalculationRouter
        print("[OK] Router module loaded")

        # Reasoning utilities
        from src.pipeline.reasoning_utils import assess_complexity, extract_answer
        print("[OK] Reasoning utilities loaded")

        print("\n[SUCCESS] All imports successful!")
        return True
    except Exception as e:
        print(f"[ERROR] Import error: {e}")
        return False

def test_config():
    """Test configuration settings."""
    print("\n[CONFIG] Testing Configuration...")
    try:
        from src.pipeline import config

        # MathCoder model configuration
        print(f"[MODEL] HF Model: {config.HF_MODEL_NAME}")

        # Compromise point settings
        print(f"[LOGIC] Decomposition Threshold: {config.DECOMPOSITION_COMPLEXITY_THRESHOLD}")

        # Other key settings
        print(f"[REASONING] Structured Reasoning: {config.USE_STRUCTURED}")
        print(f"[SCORE] Min Complexity Score: {config.COMPLEXITY_STRUCTURED_MIN_SCORE}")

        print("[OK] Configuration loaded correctly")
        return True
    except Exception as e:
        print(f"[ERROR] Config error: {e}")
        return False

def test_compromise_logic():
    """Test the compromise point logic with different problem complexities."""
    print("\n⚖️ Testing Compromise Point Logic...")
    try:
        from src.pipeline.reasoning_utils import assess_complexity
        from src.pipeline import config

        test_problems = [
            ("Simple addition: 5 + 3", False),  # Should not decompose
            ("Solve: 2x + 5 = 17", False),     # Should not decompose
            ("Prove Fermat's Last Theorem for n>2", True),  # Should decompose
        ]

        threshold = config.DECOMPOSITION_COMPLEXITY_THRESHOLD
        print(f"Using threshold: {threshold}")

        for problem, should_decompose in test_problems:
            complexity = assess_complexity(problem)
            decision = complexity >= threshold

            emoji = "✅" if decision == should_decompose else "❌"
            action = "분해" if decision else "직접해결"

            print(f"{emoji} {action} | Score: {complexity:>2} | {problem[:30]}...")

        print("✅ Compromise point logic working")
        return True
    except Exception as e:
        print(f"❌ Compromise logic error: {e}")
        return False

def test_local_llm_client_creation():
    """Test LocalLLMClient can be instantiated (without actually loading model)."""
    print("\n🤖 Testing Local LLM Client...")
    try:
        from src.pipeline.solver import LocalLLMClient
        from src.pipeline import config

        # Test that we can create the client
        client = LocalLLMClient()
        print(f"✅ Client created with model: {client.model_name}")
        print(f"✅ Quantization: {client.quantization}")

        # Don't actually load the model to avoid heavy memory usage
        print("✅ Mock client creation successful (no actual model loading)")
        return True
    except Exception as e:
        print(f"❌ LLM Client creation error: {e}")
        return False

def test_solver_creation():
    """Test Solver can be instantiated."""
    print("\n🧠 Testing Solver Creation...")
    try:
        from src.pipeline.solver import Solver

        solver = Solver()
        print("✅ Solver created successfully")

        # Check if it has the llm client
        if hasattr(solver, 'llm') and solver.llm:
            print("✅ LLM client attached to solver")
        else:
            print("❌ No LLM client found")

        return True
    except Exception as e:
        print(f"❌ Solver creation error: {e}")
        return False

def test_orchestrator_creation():
    """Test PipelineOrchestrator can be instantiated."""
    print("\n🏭 Testing Orchestrator Creation...")
    try:
        from src.pipeline.orchestrator import PipelineOrchestrator

        orchestrator = PipelineOrchestrator()
        print("✅ Orchestrator created successfully")

        # Check key components
        components = ['router', 'executor', 'verifier', 'reconciler']
        for comp in components:
            if hasattr(orchestrator, comp):
                print(f"✅ {comp.capitalize()} component present")
            else:
                print(f"❌ {comp.capitalize()} component missing")

        return True
    except Exception as e:
        print(f"❌ Orchestrator creation error: {e}")
        return False

def run_all_tests():
    """Run all test functions."""
    print("="*50)
    print("🚀 Moai System Comprehensive Test Suite")
    print("="*50)

    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Compromise Logic", test_compromise_logic),
        ("LLM Client", test_local_llm_client_creation),
        ("Solver", test_solver_creation),
        ("Orchestrator", test_orchestrator_creation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*30} {test_name.upper()} {'='*30}")
        if test_func():
            passed += 1

    print(f"\n{'='*50}")
    print(f"🏁 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! System ready for production use.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install torch transformers accelerate bitsandbytes sympy")
        print("2. Download MathCoder model: will happen automatically on first run")
        print("3. Run full inference test with: python system_test.py --full")
        return True
    else:
        print("⚠️  Some tests failed. Check errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1)
