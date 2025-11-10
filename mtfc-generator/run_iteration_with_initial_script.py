#!/usr/bin/env python3
"""
Run auto iteration system starting with a user-provided initial script
"""

import os
import json
import time
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API KEY SETUP
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
    print("Please set it in .env file or export it")
    exit(1)

print("✓ API key loaded successfully")

client = OpenAI(api_key=API_KEY)

# FILE STORAGE SETUP
SAVE_DIR = Path("mtfc_iterations")
SAVE_DIR.mkdir(exist_ok=True)

# RUBRIC DEFINITION
RUBRIC = {
    "Project Definition": 0.15,
    "Data Identification & Assessment": 0.20,
    "Mathematical Modeling": 0.25,
    "Risk Analysis": 0.20,
    "Recommendations": 0.15,
    "Communication & Clarity": 0.05
}

# SYSTEM INSTRUCTIONS
SYSTEM_PROMPT = """
You are an expert actuarial project evaluator and improver for the Modeling the Future Challenge (MTFC).

Your task:
1. Evaluate the provided MTFC actuarial script against the rubric
2. Provide 0–100 scores for each criterion with reasoning
3. Compute the weighted total using the provided weights
4. If the score <96, provide specific improvements needed
5. Rewrite the script with improvements applied

Rubric (weights in parentheses):
1. Project Definition (15%) – risk, who is at risk, mitigation strategies
2. Data Identification & Assessment (20%) – data quality, visualization, reliability
3. Mathematical Modeling (25%) – assumptions, model choice, EV or probability methods
4. Risk Analysis (20%) – quantification, likelihood × severity, comparisons
5. Recommendations (15%) – cost-benefit, actionability, linkage to model
6. Communication & Clarity (5%) – organization, visuals, tone

Scoring Bands:
90–100 = Excellent
75–89  = Good
60–74  = Adequate
<60    = Needs Work

IMPORTANT: At the end of your response, provide scores in this exact format:
SCORES:
Project Definition: [0-100]
Data Identification & Assessment: [0-100]
Mathematical Modeling: [0-100]
Risk Analysis: [0-100]
Recommendations: [0-100]
Communication & Clarity: [0-100]
WEIGHTED TOTAL: [0-100]
"""

def chat(prompt, model="gpt-4-turbo"):
    """Helper for API call"""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=4000,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Error in API call: {e}")
        raise

def extract_scores(response):
    """Pull numeric rubric scores from model output"""
    scores = {}
    total = 0
    
    scores_section_match = re.search(
        r'(?:SCORES?|RUBRIC SCORES?|EVALUATION)\s*:?\s*\n(.*?)(?:WEIGHTED TOTAL|OVERALL|TOTAL|$)', 
        response, 
        re.IGNORECASE | re.DOTALL
    )
    
    if scores_section_match:
        score_text = scores_section_match.group(1)
    else:
        score_text = response
    
    for key in RUBRIC.keys():
        key_variations = [
            key,
            key.lower(),
            key.replace(" & ", " and "),
            key.replace(" & ", " "),
        ]
        
        for key_var in key_variations:
            patterns = [
                rf"{re.escape(key_var)}\s*:?\s*(\d+(?:\.\d+)?)",
                rf"{re.escape(key_var)}\s*-\s*(\d+(?:\.\d+)?)",
                rf"{re.escape(key_var)}\s*=\s*(\d+(?:\.\d+)?)",
                rf"(\d+(?:\.\d+)?)\s*:?\s*{re.escape(key_var)}",
            ]
            
            for pattern in patterns:
                match = re.search(pattern, score_text, re.IGNORECASE)
                if match:
                    try:
                        val = float(match.group(1))
                        if 0 <= val <= 100:
                            scores[key] = val
                            break
                    except (ValueError, IndexError):
                        continue
            
            if key in scores:
                break
    
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
    
    if not total or len(scores) < len(RUBRIC):
        calculated_total = sum(scores.get(k, 0) * RUBRIC[k] for k in RUBRIC.keys())
        if calculated_total > 0:
            total = calculated_total
    
    for key in RUBRIC.keys():
        if key not in scores:
            scores[key] = 0
    
    return scores, total

def main():
    print("="*60)
    print("MTFC AUTO ITERATION SYSTEM")
    print("Starting with user-provided initial script")
    print("="*60)
    
    # Load initial script
    initial_script_path = Path("initial_script.txt")
    if not initial_script_path.exists():
        print(f"❌ ERROR: {initial_script_path} not found")
        exit(1)
    
    with open(initial_script_path, "r") as f:
        current_script = f.read()
    
    print(f"✓ Loaded initial script ({len(current_script)} characters)")
    
    iteration = 1
    overall = 0
    max_iterations = 15
    target_score = 96
    all_iterations = []
    
    print(f"\nTarget Score: {target_score}")
    print(f"Max Iterations: {max_iterations}\n")
    
    # First iteration: evaluate the provided script
    prompt = f"""Evaluate this MTFC actuarial script against the rubric:

{current_script}

Provide:
1. Detailed evaluation of each rubric category
2. Scores (0-100) for each category
3. Specific improvements needed to reach {target_score}+

Then provide an improved version of the script addressing all weaknesses.

Format scores at the end as:
SCORES:
Project Definition: [score]
Data Identification & Assessment: [score]
Mathematical Modeling: [score]
Risk Analysis: [score]
Recommendations: [score]
Communication & Clarity: [score]
WEIGHTED TOTAL: [score]"""
    
    while overall < target_score and iteration <= max_iterations:
        print(f"🌀 Iteration {iteration} started...\n")
        
        try:
            response = chat(prompt)
            scores, overall = extract_scores(response)
            
            result = {
                "iteration": iteration,
                "script": response,
                "scores": scores,
                "overall_score": overall,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            all_iterations.append(result)
            
            # Save file
            file_path = SAVE_DIR / f"iteration_{iteration}.json"
            with open(file_path, "w") as f:
                json.dump(result, f, indent=2)
            
            # Display progress
            print(f"\n{'='*60}")
            print(f"Iteration {iteration} complete — Score: {overall:.2f}/100")
            print(f"{'='*60}")
            for k, v in scores.items():
                status = "✓" if v >= 90 else "✗"
                print(f"  {status} {k}: {v:.2f}")
            
            if overall >= target_score:
                print(f"\n✅ TARGET REACHED ({overall:.2f} >= {target_score})!")
                print(f"Final script saved to: {file_path}")
                break
            
            # Prepare next iteration
            low_scores = {k: v for k, v in scores.items() if v < 90}
            if low_scores:
                feedback = f"""Revise the script to improve low-scoring areas.

Current scores:
{chr(10).join(f'- {k}: {v:.2f}' for k, v in scores.items())}

Weighted Total: {overall:.2f}/100

Areas needing improvement (scores < 90):
{chr(10).join(f'- {k}: {v:.2f}' for k, v in low_scores.items())}

Produce an improved version that:
1. Addresses all weaknesses
2. Maintains strengths
3. Includes quantitative analysis with specific numbers
4. Uses professional actuarial communication

Provide the improved script with scores at the end."""
            else:
                feedback = f"""Refine the script to reach ≥{target_score}.

Current weighted score: {overall:.2f}/100

Make final improvements:
- Enhance quantitative rigor
- Strengthen linkage between steps
- Add more detailed analysis

Provide the refined script with scores at the end."""
            
            prompt = feedback
            iteration += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error in iteration {iteration}: {e}")
            break
    
    if overall < target_score:
        print(f"\n⚠️ Maximum iterations ({max_iterations}) reached")
        print(f"Final score: {overall:.2f}/100")
    
    # Save summary
    summary = {
        "final_score": overall,
        "target_score": target_score,
        "total_iterations": iteration - 1,
        "achieved_target": overall >= target_score,
        "iterations": all_iterations
    }
    
    summary_path = SAVE_DIR / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {summary_path}")
    
    # Create FINISHED file
    finished_path = Path("FINISHED.txt")
    with open(finished_path, "w") as f:
        f.write(f"""MTFC AUTO ITERATION SYSTEM - COMPLETED

Final Score: {overall:.2f}/100
Target Score: {target_score}
Status: {'ACHIEVED' if overall >= target_score else 'NOT ACHIEVED'}
Total Iterations: {iteration - 1}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}

All iteration files saved in: {SAVE_DIR}/
Summary file: {summary_path}

Category Scores:
{chr(10).join(f'  {k}: {v:.2f}/100' for k, v in scores.items())}
""")
    
    print(f"\n✓ FINISHED file created: {finished_path}")
    print("\n" + "="*60)
    print("ITERATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

