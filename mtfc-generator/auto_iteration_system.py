"""
===========================================================
   MODELING THE FUTURE CHALLENGE — AUTO ITERATION SYSTEM
===========================================================

This program uses the OpenAI API to generate, evaluate, and 
iteratively improve MTFC actuarial scripts following the 
Actuarial Process Guide, Scenario Phase Guide, and Scenario Quest.

OBJECTIVE:
- Produce an actuarial script (project report) scoring ≥96
  according to the official MTFC rubric.

USER SETUP:
1. Replace YOUR_API_KEY_HERE with your actual key OR
   export it as an environment variable OPENAI_API_KEY.
2. Run the file.  Each iteration's output + scores are saved
   in /mtfc_iterations/iteration_N.json.

===========================================================
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

# -----------------------------------------------
# 🔑  API KEY SETUP
# -----------------------------------------------
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY not found. Please set it in .env file or as environment variable.")

client = OpenAI(api_key=API_KEY)

# -----------------------------------------------
# 🗂  FILE STORAGE SETUP
# -----------------------------------------------
SAVE_DIR = Path("mtfc_iterations")
SAVE_DIR.mkdir(exist_ok=True)

# -----------------------------------------------
# 📊  RUBRIC DEFINITION
# -----------------------------------------------
RUBRIC = {
    "Project Definition": 0.15,
    "Data Identification & Assessment": 0.20,
    "Mathematical Modeling": 0.25,
    "Risk Analysis": 0.20,
    "Recommendations": 0.15,
    "Communication & Clarity": 0.05
}

# -----------------------------------------------
# 🧮  SYSTEM INSTRUCTIONS FOR THE MODEL
# -----------------------------------------------
SYSTEM_PROMPT = """
You are an autonomous actuarial project generator and evaluator trained on:
 - The Actuarial Process Guide
 - Scenario Phase Guide
 - Scenario Quest

Your task:
1. Generate a complete actuarial project script following the 5 steps of the Actuarial Process:
   (1) Project Definition
   (2) Data Identification & Assessment
   (3) Mathematical Modeling
   (4) Risk Analysis
   (5) Recommendations
2. Evaluate your own output against the rubric below.
3. Provide 0–100 scores for each criterion and a short reasoning paragraph.
4. Compute the weighted total using the provided weights.
5. If the overall score <96, self-analyze weaknesses, rewrite, and iterate.

Rubric:
1. Project Definition (15%) – risk, who is at risk, mitigation strategies.
2. Data Identification & Assessment (20%) – data quality, visualization, reliability.
3. Mathematical Modeling (25%) – assumptions, model choice, EV or probability methods.
4. Risk Analysis (20%) – quantification, likelihood × severity, comparisons.
5. Recommendations (15%) – cost-benefit, actionability, linkage to model.
6. Communication & Clarity (5%) – organization, visuals, tone.

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

# -----------------------------------------------
# ⚙️  ITERATIVE LOOP
# -----------------------------------------------
def chat(prompt, model="gpt-4-turbo"):
    """Helper for API call using OpenAI client"""
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
        print(f"Error in API call: {e}")
        raise

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

# -----------------------------------------------
# 🚀  MAIN ITERATION
# -----------------------------------------------
def main():
    iteration = 1
    overall = 0
    max_iterations = 15
    target_score = 96
    
    # Initial prompt for scenario
    initial_prompt = """Create a full MTFC actuarial project script analyzing agricultural risk (e.g., corn yield volatility due to drought) using the Actuarial Process. 

Include:
- All 5 steps of the Actuarial Process
- Specific formulas (Expected Value, variance, etc.)
- Clear reasoning and assumptions
- Tables and quantitative examples
- Professional actuarial communication style

After generating the script, evaluate it using the rubric and provide scores at the end in the format:
SCORES:
Project Definition: [score]
Data Identification & Assessment: [score]
Mathematical Modeling: [score]
Risk Analysis: [score]
Recommendations: [score]
Communication & Clarity: [score]
WEIGHTED TOTAL: [score]"""

    prompt = initial_prompt
    all_iterations = []

    print("="*60)
    print("MODELING THE FUTURE CHALLENGE — AUTO ITERATION SYSTEM")
    print("="*60)
    print(f"Target Score: {target_score}")
    print(f"Max Iterations: {max_iterations}")
    print("="*60)

    while overall < target_score and iteration <= max_iterations:
        print(f"\n🌀 Iteration {iteration} started...\n")
        
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
                print(f"\n✅ Target reached ({overall:.2f} >= {target_score})!")
                print(f"Final script saved to: {file_path}")
                break

            # Prepare next iteration
            low_scores = {k: v for k, v in scores.items() if v < 90}
            if low_scores:
                feedback = f"""Revise the previous script to improve low-scoring rubric areas.

Current scores:
{chr(10).join(f'- {k}: {v:.2f}' for k, v in scores.items())}

Weighted Total: {overall:.2f}/100

Areas needing improvement (scores < 90):
{chr(10).join(f'- {k}: {v:.2f}' for k, v in low_scores.items())}

Produce an improved version that:
1. Addresses all weaknesses identified in the low-scoring areas
2. Maintains strengths from high-scoring areas
3. Includes all 5 steps of the Actuarial Process
4. Provides specific quantitative analysis, formulas, and examples
5. Uses professional actuarial communication

After generating the improved script, evaluate it and provide scores at the end."""
            else:
                feedback = f"""The script is close to the target. Refine it to reach ≥{target_score}.

Current weighted score: {overall:.2f}/100

Make final improvements to push the score above {target_score}:
- Enhance quantitative rigor
- Strengthen linkage between steps
- Add more detailed analysis
- Improve clarity and organization

After generating the refined script, evaluate it and provide scores at the end."""
            
            prompt = feedback
            iteration += 1
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"Error in iteration {iteration}: {e}")
            break

    if overall < target_score:
        print(f"\n⚠️ Maximum iterations ({max_iterations}) reached without achieving {target_score}+.")
        print(f"Final score: {overall:.2f}/100")
        print(f"Last iteration saved to: {SAVE_DIR / f'iteration_{iteration-1}.json'}")
    
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
    print("\n" + "="*60)
    print("ITERATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()

