#!/usr/bin/env python3
"""
MTFC Supreme Builder - Self-Optimizing to ≥98
Implements knockout gates, excellence boosters, and strict originality rules
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

SAVE_DIR = Path("mtfc_supreme")
SAVE_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = """You are an autonomous MTFC project generator and evaluator. Your sole job is to create a competition-grade actuarial script that follows the Actuarial Process (Steps 1–5), self-scores against the rubric, fixes weaknesses, and repeats until the weighted score is ≥98/100.

KNOCKOUT GATES (must pass before scoring):
1. Script organized by five Actuarial Process steps in order
2. One cohesive deliverable; every chart/table has title, caption, units, referenced in-text
3. Originality: At least 40% novel framing vs any prior draft
4. Quantification everywhere: Every claim includes a number, range, or equation

If any gate fails, fix immediately before scoring.

SCORING RUBRIC (100 pts total):
1. Project Definition (15 pts): Risk + stakeholders + 3 mitigation categories + scope + audience + success criteria
2. Data Identification & Assessment (20 pts): Data mapping, sources, reliability, ≥2 visuals
3. Mathematical Modeling (25 pts): Formal model, EV math, uncertainty metric, validation, sensitivity
4. Risk Analysis (20 pts): Likelihood × severity, baseline vs mitigation, distributional view, tail analysis
5. Recommendations (15 pts): Actionable steps, cost-benefit, all 3 mitigation categories, timeline
6. Communication & Clarity (5 pts): Clean sections, notation, consistent symbols

EXCELLENCE BOOSTERS (use ≥3):
1. Second model perspective (scenario tree or mini MC)
2. Tail focus (95th/99th percentile) and mitigation impact
3. Finance realism (capex financing/constraints)
4. Decision triggers (quantitative thresholds)
5. Portfolio effect of combined mitigations
6. Implementation risk register

TARGET: ≥98/100

SCENARIO: Farmer Jones corn farming operation - analyzing yield, price, and cost risks with mitigation strategies (irrigation, storage, insurance).

OUTPUT FORMAT: Return valid JSON with:
{
  "iteration": N,
  "scorecard": {
    "Project Definition": 0-15,
    "Data Identification & Assessment": 0-20,
    "Mathematical Modeling": 0-25,
    "Risk Analysis": 0-20,
    "Recommendations": 0-15,
    "Communication & Clarity": 0-5,
    "Excellence Boosters_Used": ["booster1", "booster2", "booster3"],
    "total": 0-100,
    "knockout_gates_passed": true/false
  },
  "script_markdown": "### Full script here...",
  "figures_and_tables": [
    {"id":"Fig1", "title":"...", "desc":"...", "units":"..."}
  ],
  "fix_plan": {
    "deductions": ["reason1", "reason2"],
    "edits_now": ["edit1", "edit2"],
    "numbers_to_add": ["number1", "number2"],
    "novelty_changes": ["change1", "change2"],
    "expected_rescore": {"Category": score}
  },
  "status": "CONTINUE" or "DONE"
}

Set status to "DONE" only when total ≥98.
"""

def chat(prompt, model="gpt-4-turbo"):
    """Call OpenAI API with system prompt"""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ API Error: {e}")
        raise

def extract_json(response):
    """Extract JSON from response, handling markdown code blocks"""
    import re
    
    # Try to find JSON in code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find JSON object directly
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

def main():
    print("="*70)
    print("MTFC SUPREME BUILDER - Target Score ≥98")
    print("="*70)
    print("Scenario: Farmer Jones Corn Farming Risk Analysis")
    print("Features: Knockout gates, Excellence boosters, Originality tracking")
    print("="*70)
    
    iteration = 1
    max_iterations = 10
    target_score = 98
    
    # Initial prompt
    prompt = """Create Iteration 1 with a complete MTFC actuarial script for Farmer Jones' corn farming operation.

SCENARIO DETAILS:
- Farmer: Farmer Jones in Iowa
- Crop: Corn (field crop)
- Risks: Yield (drought/weather), Price (volatility), Cost (input prices)
- Mitigation options: Irrigation system, on-farm grain storage, crop insurance
- Dataset context: 1994-2024 historical data for corn yields, prices, and loss causes

REQUIREMENTS:
1. Follow the 5-step Actuarial Process structure
2. Pass all knockout gates
3. Include specific numbers and calculations
4. Create at least 2 figures/tables with titles, captions, units
5. Use at least 3 Excellence Boosters
6. Provide complete self-scoring against rubric
7. If score <98, provide detailed fix plan

Generate the full JSON output with script, scorecard, figures list, and fix plan."""
    
    all_iterations = []
    
    while iteration <= max_iterations:
        print(f"\n🔬 Iteration {iteration} starting...")
        print(f"{'='*70}")
        
        try:
            response = chat(prompt)
            result = extract_json(response)
            
            if not result:
                print("❌ Failed to parse JSON response")
                print("Response preview:", response[:500])
                break
            
            # Extract scores
            scorecard = result.get("scorecard", {})
            total_score = scorecard.get("total", 0)
            status = result.get("status", "CONTINUE")
            
            # Save iteration
            iteration_file = SAVE_DIR / f"iteration_{iteration}.json"
            with open(iteration_file, "w") as f:
                json.dump(result, f, indent=2)
            
            # Display results
            print(f"\n📊 Iteration {iteration} Results")
            print(f"{'='*70}")
            print(f"Total Score: {total_score}/100 (Target: {target_score})")
            print(f"Status: {status}")
            print(f"\nCategory Breakdown:")
            for category, score in scorecard.items():
                if category not in ["Excellence Boosters_Used", "total", "knockout_gates_passed"]:
                    status_icon = "✓" if score >= (0.95 * {"Project Definition": 15, "Data Identification & Assessment": 20, "Mathematical Modeling": 25, "Risk Analysis": 20, "Recommendations": 15, "Communication & Clarity": 5}.get(category, score)) else "✗"
                    print(f"  {status_icon} {category}: {score}")
            
            boosters = scorecard.get("Excellence Boosters_Used", [])
            print(f"\nExcellence Boosters Used ({len(boosters)}): {', '.join(boosters)}")
            
            gates_passed = scorecard.get("knockout_gates_passed", True)
            print(f"Knockout Gates: {'✓ PASSED' if gates_passed else '✗ FAILED'}")
            
            # Check if done
            if total_score >= target_score and status == "DONE":
                print(f"\n{'='*70}")
                print(f"🎯 TARGET ACHIEVED: {total_score}/100 ≥ {target_score}")
                print(f"{'='*70}")
                
                # Save final script
                script = result.get("script_markdown", "")
                final_script_path = SAVE_DIR / "final_supreme_script.md"
                with open(final_script_path, "w") as f:
                    f.write(script)
                
                print(f"✓ Final script saved: {final_script_path}")
                
                # Save figures/tables
                figures = result.get("figures_and_tables", [])
                figures_path = SAVE_DIR / "figures_and_tables.json"
                with open(figures_path, "w") as f:
                    json.dump(figures, f, indent=2)
                
                print(f"✓ Figures/tables saved: {figures_path}")
                break
            
            # Prepare next iteration
            fix_plan = result.get("fix_plan", {})
            deductions = fix_plan.get("deductions", [])
            edits = fix_plan.get("edits_now", [])
            
            print(f"\n📋 Fix Plan for Next Iteration:")
            print(f"Deductions ({len(deductions)}):")
            for i, ded in enumerate(deductions[:3], 1):
                print(f"  {i}. {ded}")
            
            print(f"\nPlanned Edits ({len(edits)}):")
            for i, edit in enumerate(edits[:3], 1):
                print(f"  {i}. {edit}")
            
            # Build next prompt
            prompt = f"""Continue improving the Farmer Jones corn farming MTFC script.

CURRENT STATUS:
- Iteration: {iteration}
- Score: {total_score}/100 (need ≥{target_score})
- Knockout gates: {'PASSED' if gates_passed else 'FAILED'}

FIX PLAN FROM PREVIOUS ITERATION:
Deductions: {json.dumps(deductions, indent=2)}
Edits needed: {json.dumps(edits, indent=2)}
Numbers to add: {json.dumps(fix_plan.get('numbers_to_add', []), indent=2)}
Novelty changes: {json.dumps(fix_plan.get('novelty_changes', []), indent=2)}

REQUIREMENTS:
1. Apply ALL fixes from the plan
2. Ensure originality (change at least 40% of framing)
3. Add more quantification and specific numbers
4. Use at least 3 Excellence Boosters
5. Pass all knockout gates
6. Achieve ≥{target_score}/100

Generate the improved JSON output with updated script, scorecard, and fix plan."""
            
            iteration += 1
            all_iterations.append(result)
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"❌ Error in iteration {iteration}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    # Final summary
    summary = {
        "target_score": target_score,
        "iterations_completed": iteration - 1,
        "final_score": total_score if 'total_score' in locals() else 0,
        "achieved_target": total_score >= target_score if 'total_score' in locals() else False,
        "all_iterations": all_iterations
    }
    
    summary_path = SAVE_DIR / "supreme_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    # Create FINISHED file
    finished_path = Path("FINISHED.txt")
    with open(finished_path, "w") as f:
        f.write(f"""MTFC SUPREME BUILDER - COMPLETED

Target Score: ≥{target_score}/100
Final Score: {total_score if 'total_score' in locals() else 'N/A'}/100
Status: {'✓ ACHIEVED' if (total_score >= target_score if 'total_score' in locals() else False) else '✗ NOT ACHIEVED'}
Iterations: {iteration - 1}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}

Features Used:
- Knockout Gates validation
- Excellence Boosters (≥3)
- Originality tracking (40% novel framing)
- Comprehensive rubric scoring

Output Files:
- Final script: {SAVE_DIR}/final_supreme_script.md
- All iterations: {SAVE_DIR}/iteration_*.json
- Figures/tables: {SAVE_DIR}/figures_and_tables.json
- Summary: {summary_path}

This script is optimized for MTFC competition submission with:
- Rigorous quantification
- Professional communication
- Complete 5-step Actuarial Process
- Excellence-level analysis
""")
    
    print(f"\n{'='*70}")
    print("SUPREME BUILDER COMPLETE")
    print(f"{'='*70}")
    print(f"✓ FINISHED file created: {finished_path}")
    print(f"✓ Summary saved: {summary_path}")
    print(f"✓ All files in: {SAVE_DIR}/")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

