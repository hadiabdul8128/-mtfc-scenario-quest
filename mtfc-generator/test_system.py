#!/usr/bin/env python3
"""Test script for MTFC Generator System"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.improver import ImprovementEngine
from src.generator import ScriptGenerator
from src.evaluator import RubricEvaluator


def test_generator():
    """Test the script generator."""
    print("="*60)
    print("Testing Script Generator")
    print("="*60)
    
    try:
        generator = ScriptGenerator(model="gpt-4", provider="openai")
        scenario_data = {
            "name": "Test Scenario",
            "description": "Test risk scenario for corn farming",
            "data_sources": "Test data sources",
            "data_summary": "Test data summary",
            "model_results": "",
            "risk_analysis": ""
        }
        
        print("Generating Step 1...")
        step1 = generator.generate_step(1, scenario_data)
        print(f"Generated Step 1 ({len(step1)} characters)")
        print(step1[:200] + "...")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_evaluator():
    """Test the rubric evaluator."""
    print("\n" + "="*60)
    print("Testing Rubric Evaluator")
    print("="*60)
    
    try:
        evaluator = RubricEvaluator(model="gpt-4", provider="openai")
        test_report = """
        # MTFC Actuarial Analysis Report
        
        ## 1. Project Definition
        Risk: Corn yield volatility due to drought.
        Stakeholders: Farmers, insurance companies.
        Mitigation: Irrigation systems.
        
        ## 2. Data Identification
        Data sources: FCIC Cause of Loss dataset.
        Frequency: 12 of 30 years.
        Severity: $425 per acre.
        """
        
        print("Evaluating test report...")
        result = evaluator.evaluate_report(test_report)
        print(f"Weighted Total: {result['weighted_total']:.2f}/100")
        print("Category Scores:")
        for category, score in result['scores'].items():
            print(f"  {category}: {score}/100")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_improvement_engine():
    """Test the improvement engine (single iteration)."""
    print("\n" + "="*60)
    print("Testing Improvement Engine")
    print("="*60)
    
    try:
        engine = ImprovementEngine(model="gpt-4", provider="openai")
        engine.max_iterations = 1  # Just test one iteration
        
        scenario_data = {
            "name": "Test Scenario",
            "description": "Test risk scenario",
            "data_sources": "Test data",
            "data_summary": "Test summary",
            "model_results": "",
            "risk_analysis": ""
        }
        
        print("Generating and evaluating report (1 iteration)...")
        result = engine.generate_and_improve(scenario_data)
        print(f"Final Weighted Total: {result['final_weighted_total']:.2f}/100")
        print(f"Total Iterations: {result['total_iterations']}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("MTFC Generator System Test Suite")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        sys.exit(1)
    
    results = []
    
    # Test individual components
    print("\n1. Testing Generator...")
    results.append(("Generator", test_generator()))
    
    print("\n2. Testing Evaluator...")
    results.append(("Evaluator", test_evaluator()))
    
    print("\n3. Testing Improvement Engine (1 iteration)...")
    results.append(("Improvement Engine", test_improvement_engine()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for component, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{component}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()

