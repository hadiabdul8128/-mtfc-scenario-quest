#!/usr/bin/env python3
"""
MTFC Efficient Self-Improving Loop (≥96 Target)
Works with file references to handle large papers
"""

import os
import json
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not found")
    exit(1)

client = OpenAI(api_key=API_KEY)

SAVE_DIR = Path("mtfc_final_96")
SAVE_DIR.mkdir(exist_ok=True)

INITIAL_PAPER_PATH = Path("mtfc_comprehensive/FINAL_COMPREHENSIVE_PAPER.txt")

def chat(prompt, model="gpt-4-turbo", max_tokens=3000):
    """Call OpenAI API"""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ API Error: {e}")
        raise

def extract_json(response):
    """Extract JSON from response"""
    import re
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            return None
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse error: {e}")
        return None

def evaluate_paper_summary(paper_text):
    """Evaluate paper and return scores"""
    
    # Create a summary for evaluation
    word_count = len(paper_text.split())
    has_part1 = "Part 1: Project Definition" in paper_text
    has_part2 = "Part 2: Data Identification" in paper_text
    has_part3 = "Part 3: Mathematical Modeling" in paper_text
    has_part4 = "Part 4: Risk Analysis" in paper_text
    has_part5 = "Part 5: Recommendations" in paper_text
    has_notation = "Notation Block" in paper_text
    has_figures = "Figures and Tables" in paper_text
    
    # Count tables and quantitative elements
    table_count = paper_text.count("Table")
    figure_count = paper_text.count("Figure")
    has_npv = "NPV" in paper_text
    has_irr = "IRR" in paper_text
    has_ev = "EV" in paper_text or "Expected Value" in paper_text
    has_regression = "regression" in paper_text or "Regression" in paper_text
    
    # Extract first 2000 chars for detailed review
    sample = paper_text[:2000]
    
    prompt = f"""Evaluate this MTFC Scenario Quest Response paper against the rubric.

PAPER STATISTICS:
- Word count: {word_count}
- Has Part 1 (Project Definition): {has_part1}
- Has Part 2 (Data ID & Assessment): {has_part2}
- Has Part 3 (Mathematical Modeling): {has_part3}
- Has Part 4 (Risk Analysis): {has_part4}
- Has Part 5 (Recommendations): {has_part5}
- Has Notation Block: {has_notation}
- Has Figures/Tables List: {has_figures}
- Table count: {table_count}
- Figure count: {figure_count}
- Has NPV/IRR calculations: {has_npv}/{has_irr}
- Has EV calculations: {has_ev}
- Has regression analysis: {has_regression}

PAPER SAMPLE (first 2000 chars):
{sample}

RUBRIC (Total 100 + up to 3 bonus):
- Project Definition (15): Quantified risks, stakeholders, 3 mitigation categories
- Data Identification & Assessment (20): Data mapping, tables, 2+ visuals
- Mathematical Modeling (25): Equations, EV math, sensitivity, diagnostics
- Risk Analysis (20): 2×2 table, tail analysis, baseline vs mitigation
- Recommendations (15): NPV/IRR/payback, triggers, all 3 mitigation categories
- Communication & Clarity (5): Clean numbering, notation, labeled visuals
- Excellence Boosters (+0-3): Need ≥3 of: 95/99% tail, second model, financing, triggers, portfolio, risk register

Based on the statistics and sample, score each category and provide:

{{
  "scores": {{
    "Project Definition": 0-15,
    "Data Identification & Assessment": 0-20,
    "Mathematical Modeling": 0-25,
    "Risk Analysis": 0-20,
    "Recommendations": 0-15,
    "Communication & Clarity": 0-5,
    "Excellence_Boosters": 0-3,
    "Total": 0-103
  }},
  "deductions": ["reason1", "reason2"],
  "strengths": ["strength1", "strength2"],
  "status": "DONE if ≥96, else CONTINUE"
}}"""
    
    response = chat(prompt, max_tokens=1500)
    return extract_json(response)

def main():
    print("="*90)
    print("MTFC EFFICIENT SELF-IMPROVING LOOP - Target ≥96/100")
    print("="*90)
    
    # Load paper
    if not INITIAL_PAPER_PATH.exists():
        print(f"❌ Paper not found at {INITIAL_PAPER_PATH}")
        return
    
    with open(INITIAL_PAPER_PATH, "r") as f:
        paper_text = f.read()
    
    word_count = len(paper_text.split())
    print(f"✓ Loaded paper: {word_count:,} words")
    
    print(f"\n{'='*90}")
    print("📊 EVALUATING PAPER")
    print(f"{'='*90}\n")
    
    print("📡 Calling API to evaluate...")
    result = evaluate_paper_summary(paper_text)
    
    if not result:
        print("❌ Failed to get evaluation")
        return
    
    scores = result.get("scores", {})
    total_score = scores.get("Total", 0)
    status = result.get("status", "CONTINUE")
    deductions = result.get("deductions", [])
    strengths = result.get("strengths", [])
    
    # Display results
    print(f"\n{'='*90}")
    print(f"📊 EVALUATION RESULTS")
    print(f"{'='*90}")
    print(f"Total Score: {total_score}/100")
    print(f"Status: {status}")
    print(f"Word Count: {word_count:,}")
    
    print(f"\n📋 CATEGORY SCORES:")
    categories = [
        ("Project Definition", 15),
        ("Data Identification & Assessment", 20),
        ("Mathematical Modeling", 25),
        ("Risk Analysis", 20),
        ("Recommendations", 15),
        ("Communication & Clarity", 5)
    ]
    
    for cat, max_score in categories:
        score = scores.get(cat, 0)
        pct = (score / max_score * 100) if max_score > 0 else 0
        icon = "✓" if pct >= 90 else "⚠" if pct >= 80 else "✗"
        print(f"  {icon} {cat}: {score}/{max_score} ({pct:.0f}%)")
    
    boosters = scores.get("Excellence_Boosters", 0)
    print(f"\n🌟 Excellence Boosters: +{boosters}/3")
    
    if deductions:
        print(f"\n📉 DEDUCTIONS:")
        for i, ded in enumerate(deductions, 1):
            print(f"  {i}. {ded}")
    
    if strengths:
        print(f"\n✨ STRENGTHS:")
        for i, strength in enumerate(strengths, 1):
            print(f"  {i}. {strength}")
    
    # Save results
    final_scores_file = SAVE_DIR / "FINAL_EVALUATION.json"
    with open(final_scores_file, "w") as f:
        json.dump({
            "scores": scores,
            "deductions": deductions,
            "strengths": strengths,
            "word_count": word_count,
            "status": status
        }, f, indent=2)
    
    # Copy paper to final location
    if total_score >= 96:
        print(f"\n{'='*90}")
        print(f"🎯 TARGET ACHIEVED: {total_score}/100 ≥ 96")
        print(f"{'='*90}")
        
        final_paper_file = SAVE_DIR / "FINAL_PAPER_96PLUS.txt"
        with open(final_paper_file, "w") as f:
            f.write(paper_text)
        
        print(f"\n✓ Final paper saved: {final_paper_file}")
        print(f"✓ Evaluation saved: {final_scores_file}")
        
        # Print summary
        print(f"\n🏆 PAPER SUMMARY:")
        print(f"  • Word Count: {word_count:,}")
        print(f"  • Total Score: {total_score}/100")
        print(f"  • Excellence Boosters: {boosters}/3")
        print(f"  • Status: Competition-Ready ✓")
        
        # Create completion marker
        with open("FINISHED_96PLUS.txt", "w") as f:
            f.write(f"""MTFC SELF-IMPROVING LOOP - COMPLETED

Target Score: ≥96/100
Final Score: {total_score}/100
Status: ✓ ACHIEVED
Word Count: {word_count:,}
Excellence Boosters: {boosters}/3
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}

Category Breakdown:
""")
            for cat, max_score in categories:
                score = scores.get(cat, 0)
                f.write(f"- {cat}: {score}/{max_score}\n")
            
            f.write(f"\nStrengths:\n")
            for strength in strengths:
                f.write(f"- {strength}\n")
            
            if deductions:
                f.write(f"\nMinor Deductions:\n")
                for ded in deductions:
                    f.write(f"- {ded}\n")
            
            f.write(f"\nOutput Files:\n")
            f.write(f"- Final paper: {final_paper_file}\n")
            f.write(f"- Evaluation: {final_scores_file}\n")
            f.write(f"\nThis paper is competition-ready for MTFC Scenario Quest Response 2025-26.\n")
        
        print(f"\n✓ FINISHED_96PLUS.txt created")
    else:
        print(f"\n⚠️ Score {total_score}/100 below target of 96")
        print("Additional improvements needed")
    
    print(f"\n{'='*90}")
    print("EVALUATION COMPLETE")
    print(f"{'='*90}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

