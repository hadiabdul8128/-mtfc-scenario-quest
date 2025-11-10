#!/usr/bin/env python3
"""Test script for auto_iteration_system score extraction"""

import re

# Copy of extract_scores function for testing
RUBRIC = {
    "Project Definition": 0.15,
    "Data Identification & Assessment": 0.20,
    "Mathematical Modeling": 0.25,
    "Risk Analysis": 0.20,
    "Recommendations": 0.15,
    "Communication & Clarity": 0.05
}

def extract_scores(response):
    """Pull numeric rubric scores from model output"""
    scores = {}
    total = 0
    
    # Try to find scores section - look for "SCORES" or "SCORE" header
    scores_section_match = re.search(
        r'(?:SCORES?|RUBRIC SCORES?|EVALUATION)\s*:?\s*\n(.*?)(?:WEIGHTED TOTAL|OVERALL|TOTAL|$)', 
        response, 
        re.IGNORECASE | re.DOTALL
    )
    
    if scores_section_match:
        score_text = scores_section_match.group(1)
    else:
        # If no scores section found, search entire response
        score_text = response
    
    # Extract scores for each rubric category
    for key in RUBRIC.keys():
        # Create flexible patterns - handle various formats
        key_variations = [
            key,  # Full key
            key.lower(),  # Lowercase
            key.replace(" & ", " and "),  # "and" instead of "&"
            key.replace(" & ", " "),  # Without "&"
        ]
        
        # Try different patterns for each variation
        for key_var in key_variations:
            patterns = [
                rf"{re.escape(key_var)}\s*:?\s*(\d+(?:\.\d+)?)",  # "Category: 85"
                rf"{re.escape(key_var)}\s*-\s*(\d+(?:\.\d+)?)",  # "Category - 85"
                rf"{re.escape(key_var)}\s*=\s*(\d+(?:\.\d+)?)",  # "Category = 85"
                rf"(\d+(?:\.\d+)?)\s*:?\s*{re.escape(key_var)}",  # "85: Category"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, score_text, re.IGNORECASE)
                if match:
                    try:
                        val = float(match.group(1))
                        # Only accept reasonable scores
                        if 0 <= val <= 100:
                            scores[key] = val
                            break
                    except (ValueError, IndexError):
                        continue
            
            if key in scores:
                break
    
    # Extract weighted total - look for various formats
    total_patterns = [
        r'WEIGHTED TOTAL\s*:?\s*(\d+(?:\.\d+)?)',
        r'OVERALL SCORE\s*:?\s*(\d+(?:\.\d+)?)',
        r'TOTAL SCORE\s*:?\s*(\d+(?:\.\d+)?)',
        r'FINAL SCORE\s*:?\s*(\d+(?:\.\d+)?)',
        r'WEIGHTED\s*:?\s*(\d+(?:\.\d+)?)',
    ]
    
    for pattern in total_patterns:
        total_match = re.search(pattern, response, re.IGNORECASE)
        if total_match:
            try:
                total = float(total_match.group(1))
                if 0 <= total <= 100:
                    break
            except (ValueError, IndexError):
                continue
    
    # Calculate weighted total from individual scores if not found or incomplete
    if not total or len(scores) < len(RUBRIC):
        calculated_total = sum(scores.get(k, 0) * RUBRIC[k] for k in RUBRIC.keys())
        if calculated_total > 0:
            total = calculated_total
    
    # Fill in missing scores with 0 for display
    for key in RUBRIC.keys():
        if key not in scores:
            scores[key] = 0
    
    return scores, total

def test_score_extraction():
    """Test the score extraction function"""
    print("Testing Score Extraction...")
    print("="*60)
    
    # Test case 1: Standard format
    test1 = """SCORES:
Project Definition: 85
Data Identification & Assessment: 90
Mathematical Modeling: 88
Risk Analysis: 92
Recommendations: 87
Communication & Clarity: 95
WEIGHTED TOTAL: 88.5"""
    
    scores1, total1 = extract_scores(test1)
    print(f"\nTest 1 - Standard Format:")
    print(f"  Scores found: {len([s for s in scores1.values() if s > 0])}/{len(RUBRIC)}")
    print(f"  Weighted total: {total1:.2f}")
    assert len([s for s in scores1.values() if s > 0]) == 6, "Should find 6 scores"
    assert total1 > 0, "Should have weighted total"
    print("  ✓ PASSED")
    
    # Test case 2: Alternative format
    test2 = """Evaluation Results:
Project Definition - 78.5
Data Identification and Assessment: 82.0
Mathematical Modeling = 85
Risk Analysis: 80
Recommendations: 83
Communication & Clarity: 90
OVERALL SCORE: 82.8"""
    
    scores2, total2 = extract_scores(test2)
    print(f"\nTest 2 - Alternative Format:")
    print(f"  Scores found: {len([s for s in scores2.values() if s > 0])}/{len(RUBRIC)}")
    print(f"  Weighted total: {total2:.2f}")
    assert len([s for s in scores2.values() if s > 0]) >= 5, "Should find at least 5 scores"
    print("  ✓ PASSED")
    
    # Test case 3: Missing some scores
    test3 = """SCORES:
Project Definition: 90
Mathematical Modeling: 85
Risk Analysis: 88
WEIGHTED TOTAL: 87.5"""
    
    scores3, total3 = extract_scores(test3)
    print(f"\nTest 3 - Partial Scores:")
    print(f"  Scores found: {len([s for s in scores3.values() if s > 0])}/{len(RUBRIC)}")
    print(f"  Weighted total: {total3:.2f}")
    assert total3 > 0, "Should calculate total from available scores"
    print("  ✓ PASSED")
    
    print("\n" + "="*60)
    print("All tests passed! ✓")
    print("="*60)

if __name__ == "__main__":
    test_score_extraction()

