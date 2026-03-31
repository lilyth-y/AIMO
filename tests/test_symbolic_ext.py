import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'src')))

from pipeline.answer_extraction import AnswerExtractor

def test_normalization():
    extractor = AnswerExtractor()
    
    # Test cases: (input_text, expected_normalized)
    test_cases = [
        ("π", "pi"),
        ("√2", "sqrt2"),
        ("1/2", "1/2"),
        ("½", "1/2"),
        ("x² + y³", "x**2 + y**3"),
        ("30°", "30*pi/180"),
        ("∞", "oo"),
    ]
    
    print("--- Running Normalization Tests ---")
    for inp, exp in test_cases:
        norm = extractor.normalize_math_text(inp)
        status = "PASS" if norm == exp else f"FAIL (Got: {norm})"
        print(f"Input: {inp} | Expected: {exp} | Result: {status}")

def test_extraction():
    extractor = AnswerExtractor()
    
    # Test cases: (full_text, expected_value)
    test_cases = [
        ("<ANS> π </ANS>", "pi"),
        ("<ANS> 1/2 </ANS>", 0.5),
        ("<ANS> √4 </ANS>", 2.0),
    ]
    
    print("\n--- Running Extraction Tests ---")
    for text, exp in test_cases:
        result = extractor.extract_from_text(text)
        val = result.value
        
        # Simple string comparison first
        if str(val) == str(exp):
            status = "PASS"
        else:
            # Numeric comparison fallback
            try:
                # If it's a SymPy object, try evaluating to float
                actual_num = float(val.evalf()) if hasattr(val, 'evalf') else float(val)
                expected_num = float(exp)
                status = "PASS" if abs(actual_num - expected_num) < 1e-9 else f"FAIL (Got: {val})"
            except:
                status = f"FAIL (Got: {val})"
                
        print(f"Text: {text} | Expected: {exp} | Result: {status}")

if __name__ == "__main__":
    try:
        test_normalization()
        test_extraction()
    except Exception as e:
        print(f"Test crashed: {e}")
        import traceback
        traceback.print_exc()
