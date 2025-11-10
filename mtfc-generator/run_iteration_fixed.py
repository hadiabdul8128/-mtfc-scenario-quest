#!/usr/bin/env python3
"""
Run auto iteration system with proper scenario retention
"""

import os
import json
import time
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not found")
    exit(1)

print("✓ API key loaded")

client = OpenAI(api_key=API_KEY)

SAVE_DIR = Path("mtfc_iterations_fixed")
SAVE_DIR.mkdir(exist_ok=True)

RUBRIC = {
    "Project Definition": 0.15,
    "Data Identification & Assessment": 0.20,
    "Mathematical Modeling": 0.25,
    "Risk Analysis": 0.20,
    "Recommendations": 0.15,
    "Communication & Clarity": 0.05
}

SYSTEM_PROMPT = """
You are an expert MTFC actuarial evaluator. Your job is to:
1. Evaluate the provided script against the rubric
2. Identify weaknesses and areas for improvement
3. Improve the SAME script (keep the same scenario, topic, and structure)
4. Add specific numbers, calculations, and quantitative analysis
5. Enhance clarity and organization

CRITICAL: Do NOT change the scenario topic. If the script is about corn farming, keep it about corn farming. Only improve the existing content.

Rubric (weights):
- Project Definition (15%): risk, stakeholders, mitigation
- Data Identification & Assessment (20%): data quality, sources, analysis  
- Mathematical Modeling (25%): formulas, calculations, assumptions
- Risk Analysis (20%): quantification, scenarios, comparisons
- Recommendations (15%): cost-benefit, actionability, linkage
- Communication & Clarity (5%): organization, presentation

Provide scores at the end:
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
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=4000,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ API Error: {e}")
        raise

def extract_scores(response):
    scores = {}
    total = 0
    
    score_section = re.search(
        r'(?:SCORES?|EVALUATION)\s*:?\s*\n(.*?)(?:WEIGHTED TOTAL|$)', 
        response, 
        re.IGNORECASE | re.DOTALL
    )
    
    score_text = score_section.group(1) if score_section else response
    
    for key in RUBRIC.keys():
        for key_var in [key, key.lower(), key.replace(" & ", " and ")]:
            patterns = [
                rf"{re.escape(key_var)}\s*:?\s*(\d+(?:\.\d+)?)",
                rf"(\d+(?:\.\d+)?)\s*/\s*100",
            ]
            
            for pattern in patterns:
                match = re.search(pattern, score_text, re.IGNORECASE)
                if match:
                    try:
                        val = float(match.group(1))
                        if 0 <= val <= 100:
                            scores[key] = val
                            break
                    except:
                        pass
            if key in scores:
                break
    
    for pattern in [r'WEIGHTED TOTAL\s*:?\s*(\d+(?:\.\d+)?)', r'OVERALL.*?(\d+(?:\.\d+)?)']:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            try:
                total = float(match.group(1))
                if 0 <= total <= 100:
                    break
            except:
                pass
    
    if not total:
        total = sum(scores.get(k, 0) * RUBRIC[k] for k in RUBRIC.keys())
    
    for key in RUBRIC.keys():
        if key not in scores:
            scores[key] = 0
    
    return scores, total

def main():
    print("="*60)
    print("MTFC AUTO ITERATION - SCENARIO RETAINED")
    print("="*60)
    
    script_path = Path("initial_script.txt")
    with open(script_path) as f:
        current_script = f.read()
    
    print(f"✓ Loaded script ({len(current_script)} chars)")
    print(f"Topic: Farmer Jones corn farming risk analysis\n")
    
    iteration = 1
    overall = 0
    target = 96
    max_iter = 15
    all_iterations = []
    
    # First evaluation
    prompt = f"""Evaluate this MTFC script about Farmer Jones' corn farming operation:

{current_script}

This script analyzes corn farming risks (yield, price, cost) and mitigation strategies (irrigation, storage, insurance).

Task:
1. Evaluate each rubric category
2. Provide specific scores
3. Identify weaknesses
4. Create an IMPROVED version of THIS SAME SCRIPT
   - Keep it about Farmer Jones and corn farming
   - Add specific numbers where indicated (from typical corn farming data)
   - Enhance calculations and formulas
   - Improve clarity and organization
   - Fill in the "[INSERT]" placeholders with example values

Provide the IMPROVED script followed by scores."""
    
    while overall < target and iteration <= max_iter:
        print(f"🌀 Iteration {iteration}...")
        
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
            
            file_path = SAVE_DIR / f"iteration_{iteration}.json"
            with open(file_path, "w") as f:
                json.dump(result, f, indent=2)
            
            print(f"\n{'='*60}")
            print(f"Iteration {iteration} - Score: {overall:.2f}/100")
            print(f"{'='*60}")
            for k, v in scores.items():
                status = "✓" if v >= 90 else "✗"
                print(f"  {status} {k}: {v:.2f}")
            
            if overall >= target:
                print(f"\n✅ TARGET REACHED ({overall:.2f} >= {target})!")
                
                # Extract just the script part (remove evaluation)
                script_match = re.search(r'(?:IMPROVED.*?SCRIPT|MTFC.*?Response)(.*?)(?:SCORES?:|$)', response, re.IGNORECASE | re.DOTALL)
                final_script = script_match.group(1).strip() if script_match else response
                
                # Save clean final script
                final_path = SAVE_DIR / "final_script.txt"
                with open(final_path, "w") as f:
                    f.write(final_script)
                
                print(f"Final script saved to: {final_path}")
                break
            
            # Next iteration
            low = {k: v for k, v in scores.items() if v < 90}
            
            if low:
                feedback = f"""Improve the Farmer Jones corn farming script further.

Current scores:
{chr(10).join(f'- {k}: {v:.2f}' for k, v in scores.items())}

Weighted: {overall:.2f}/100

Low-scoring areas:
{chr(10).join(f'- {k}: {v:.2f} - needs more detail/numbers' for k, v in low.items())}

Task: Enhance the SAME Farmer Jones corn farming script:
1. Add more specific calculations and numbers
2. Strengthen weak areas above  
3. Keep the scenario (Farmer Jones, corn, Iowa)
4. Add quantitative examples
5. Improve formulas and analysis

Provide the improved script with scores."""
            else:
                feedback = f"""Final refinement of Farmer Jones script to reach {target}+.

Current: {overall:.2f}/100

Make final enhancements:
- More quantitative rigor
- Stronger linkages
- More detailed analysis
- Professional presentation

Provide refined script with scores."""
            
            prompt = feedback
            iteration += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    
    # Summary
    summary = {
        "final_score": overall,
        "target_score": target,
        "total_iterations": iteration - 1,
        "achieved": overall >= target,
        "iterations": all_iterations
    }
    
    summary_path = SAVE_DIR / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    # FINISHED file
    finished = Path("FINISHED.txt")
    with open(finished, "w") as f:
        f.write(f"""MTFC AUTO ITERATION - COMPLETED

Scenario: Farmer Jones Corn Farming Risk Analysis
Final Score: {overall:.2f}/100
Target: {target}
Status: {'✓ ACHIEVED' if overall >= target else '✗ NOT ACHIEVED'}
Iterations: {iteration - 1}
Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

Files:
- Final script: {SAVE_DIR}/final_script.txt
- All iterations: {SAVE_DIR}/
- Summary: {summary_path}

Category Scores:
{chr(10).join(f'  {k}: {v:.2f}/100' for k, v in scores.items())}

INSTRUCTIONS:
Review the final script in: {SAVE_DIR}/final_script.txt
This is your improved Farmer Jones corn farming analysis ready for MTFC submission.
""")
    
    print(f"\n✓ FINISHED file created")
    print(f"✓ Final script: {SAVE_DIR}/final_script.txt")
    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

