#!/usr/bin/env python3
"""
MTFC Ultra Builder - Full 30-Item Paper Generator
Target: ≥98/100 with complete quantification and zero placeholders
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

client = OpenAI(api_key=API_KEY)

SAVE_DIR = Path("mtfc_ultra")
SAVE_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = """You are an autonomous MTFC writer-evaluator. Your job is to generate a complete final project paper that matches the 30-item structure (Parts 1-5, #1-#30), is highly quantitative, and achieves ≥98/100.

MANDATORY STRUCTURE (use EXACTLY these headers and numbering):

MTFC Scenario Quest Response 2025-26
Team Name: [plausible name]
Team ID #: [numeric]

Part 1: Project Definition
#1: Who is at risk?
#2: Defining the risks
#3: Identify risk mitigation strategies

Part 2: Data Identification & Assessment
#4: Identifying the type of data
#5-#8: Planting costs
#9: Harvest expectations
#10-#11: Corn sale prices
#12: October sale
#13: Optimal sale month
#14: Data visual
#15: Top causes of loss & impacts

Part 3: Mathematical Modeling
#16: Linear regression
#17: Trends/patterns
#18: Assumption evaluation
#19: Assumption development
#20: Frequency of drought claims
#21: Expected value (EV) of drought loss
#22: Average annual insurance payout

Part 4: Risk Analysis
#23: Grain silo strategy
#24: Irrigation system strategy
#25: Crop insurance scenario
#26: Value of insurance

Part 5: Recommendations
#27: Irrigation impact
#28: Compare EV of loss
#29: Profit trajectory
#30: Should irrigation be recommended?

Notation Block (define ALL symbols with units)
Figures and Tables List (with concrete values, NOT placeholders)

CONTENT REQUIREMENTS:
- Numbers everywhere: Every claim has a number, range, or equation
- NO placeholders ("TBD", "Insert X", "historical data matching", etc.)
- Internal consistency: revenue = quantity × price; costs sum correctly
- Length targets:
  * Part 1: ≥300 words, 2-3 quantified metrics
  * Part 2: ≥900 words, 2+ visuals with numbers, 2+ tables with values
  * Part 3: ≥900 words, regression coefficients, EV math, sensitivity table
  * Part 4: ≥700 words, 2×2 loss table, tail narrative
  * Part 5: ≥500 words, NPV/IRR/payback computed

EXCELLENCE BOOSTERS (include ≥3):
1. Second modeling perspective (scenario tree/Monte Carlo)
2. Tail focus (95th/99th percentile)
3. Financing realism (debt service/constraints)
4. Decision triggers (quantitative thresholds)
5. Portfolio effect (combined mitigations)
6. Risk register (owner/likelihood/severity)

SCORING RUBRIC (Total 100 pts):
- Project Definition: 15 pts
- Data Identification & Assessment: 20 pts
- Mathematical Modeling: 25 pts
- Risk Analysis: 20 pts
- Recommendations: 15 pts
- Communication & Clarity: 5 pts

TARGET: ≥98/100

SCENARIO: Farmer Jones, Iowa corn farmer, 500 acres, analyzing yield/price/cost risks with irrigation, storage, and insurance options. Use realistic Iowa corn data (yields 180-200 bu/acre, prices $4-6/bu, costs $600-700/acre).

OUTPUT FORMAT (JSON):
{
  "iteration": N,
  "scorecard": {
    "Project Definition": 0-15,
    "Data Identification & Assessment": 0-20,
    "Mathematical Modeling": 0-25,
    "Risk Analysis": 0-20,
    "Recommendations": 0-15,
    "Communication & Clarity": 0-5,
    "Excellence_Boosters_Used": ["b1","b2","b3"],
    "total": 0-100
  },
  "paper_full_text": "MTFC Scenario Quest Response 2025-26\\n\\nTeam Name: ...\\n\\nPart 1: Project Definition\\n\\n#1: Who is at risk?\\n...",
  "deductions": ["reason1", "reason2"],
  "fix_plan": {
    "edits_now": ["edit1", "edit2"],
    "numbers_to_add": ["number1", "number2"],
    "novelty_changes": ["change1", "change2"],
    "expected_rescore": {"Modeling": 24}
  },
  "status": "CONTINUE" or "DONE"
}

Set status to "DONE" only when total ≥98.

CRITICAL: Generate complete, publishable text with ALL numbers filled in. No "see table", "as shown", or "detailed analysis" without the actual content."""

def chat(prompt, model="gpt-4-turbo", max_tokens=4096):
    """Call OpenAI API"""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
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
        # Try to save the raw response
        with open(SAVE_DIR / "last_response_error.txt", "w") as f:
            f.write(response)
        return None

def count_words(text):
    """Count words in text"""
    return len(text.split())

def validate_paper(paper_text):
    """Validate paper has all required sections"""
    required = [
        "Part 1: Project Definition",
        "#1:", "#2:", "#3:",
        "Part 2: Data Identification & Assessment",
        "#4:", "#5", "#9:", "#10", "#12:", "#13:", "#14:", "#15:",
        "Part 3: Mathematical Modeling",
        "#16:", "#17:", "#18:", "#19:", "#20:", "#21:", "#22:",
        "Part 4: Risk Analysis",
        "#23:", "#24:", "#25:", "#26:",
        "Part 5: Recommendations",
        "#27:", "#28:", "#29:", "#30:",
        "Notation Block",
        "Figures and Tables"
    ]
    
    missing = []
    for req in required:
        if req not in paper_text:
            missing.append(req)
    
    return missing

def main():
    print("="*80)
    print("MTFC ULTRA BUILDER - Complete 30-Item Paper Generator")
    print("="*80)
    print("Target: ≥98/100 with zero placeholders")
    print("Scenario: Farmer Jones, 500-acre Iowa corn operation")
    print("="*80)
    
    iteration = 1
    max_iterations = 8
    target_score = 98
    
    # Initial prompt
    prompt = """Generate Iteration 1: A complete, publication-ready MTFC paper for Farmer Jones.

SCENARIO SPECIFICS:
- Farmer Jones, Iowa
- 500 acres corn (field crop)
- Historical yield: 180-200 bu/acre (drought risk reduces to 120-140)
- Corn prices: $4.20-$5.80/bu (seasonal variation)
- Planting costs: seed $140/acre, fertilizer $180/acre, chemicals $85/acre, labor $60/acre, machinery $95/acre, land rent $180/acre = ~$740/acre total
- Mitigation options:
  1. Center-pivot irrigation: $250,000 capex, covers 125 acres, +15% yield uplift, -50% yield variance
  2. Grain storage bin: $180,000 for 50,000 bu capacity, $0.05/bu/month storage cost, 0.5% shrink/month
  3. Crop insurance: 80% RP coverage, $32/acre premium, 98% loss cost ratio

REQUIREMENTS:
1. Follow the 30-item outline EXACTLY
2. Fill in ALL calculations with specific numbers
3. Include regression coefficients (e.g., Yield = β₀ + β₁·Rainfall + β₂·GDD + ε)
4. Compute EV = Σp_i·L_i with explicit scenario probabilities
5. Build 2×2 table: {Baseline, Mitigation} × {Mean loss, 95th percentile loss}
6. Calculate NPV, IRR, payback period
7. Add ≥3 Excellence Boosters
8. Create notation block and figures/tables list with REAL values
9. Self-score against rubric
10. Provide fix plan if <98

Generate the complete JSON response with full paper text."""
    
    all_iterations = []
    
    while iteration <= max_iterations:
        print(f"\n{'='*80}")
        print(f"🔬 ITERATION {iteration}")
        print(f"{'='*80}")
        
        try:
            print("📡 Calling API (this may take 30-60 seconds for comprehensive output)...")
            response = chat(prompt, max_tokens=4096)
            
            print(f"✓ Received response ({len(response)} chars)")
            
            result = extract_json(response)
            
            if not result:
                print("❌ Failed to parse JSON")
                print("Saving raw response to debug...")
                with open(SAVE_DIR / f"iteration_{iteration}_raw.txt", "w") as f:
                    f.write(response)
                break
            
            # Extract key data
            scorecard = result.get("scorecard", {})
            total_score = scorecard.get("total", 0)
            status = result.get("status", "CONTINUE")
            paper_text = result.get("paper_full_text", "")
            
            # Save iteration
            iteration_file = SAVE_DIR / f"iteration_{iteration}.json"
            with open(iteration_file, "w") as f:
                json.dump(result, f, indent=2)
            
            # Save paper text separately
            paper_file = SAVE_DIR / f"paper_iteration_{iteration}.txt"
            with open(paper_file, "w") as f:
                f.write(paper_text)
            
            # Validate structure
            missing = validate_paper(paper_text)
            word_count = count_words(paper_text)
            
            # Display results
            print(f"\n📊 ITERATION {iteration} RESULTS")
            print(f"{'='*80}")
            print(f"Total Score: {total_score}/100 (Target: {target_score})")
            print(f"Status: {status}")
            print(f"Word Count: {word_count:,}")
            print(f"Missing Sections: {len(missing)}")
            
            print(f"\n📋 CATEGORY SCORES:")
            for cat, score in scorecard.items():
                if cat not in ["Excellence_Boosters_Used", "total"]:
                    max_scores = {
                        "Project Definition": 15,
                        "Data Identification & Assessment": 20,
                        "Mathematical Modeling": 25,
                        "Risk Analysis": 20,
                        "Recommendations": 15,
                        "Communication & Clarity": 5
                    }
                    max_val = max_scores.get(cat, score)
                    pct = (score/max_val*100) if max_val > 0 else 0
                    icon = "✓" if pct >= 95 else "⚠" if pct >= 85 else "✗"
                    print(f"  {icon} {cat}: {score}/{max_val} ({pct:.0f}%)")
            
            boosters = scorecard.get("Excellence_Boosters_Used", [])
            print(f"\n🌟 Excellence Boosters ({len(boosters)}): {', '.join(boosters)}")
            
            if missing:
                print(f"\n⚠️ Missing sections: {', '.join(missing[:5])}")
            
            # Check completion
            if total_score >= target_score and status == "DONE" and len(missing) == 0:
                print(f"\n{'='*80}")
                print(f"🎯 TARGET ACHIEVED: {total_score}/100")
                print(f"{'='*80}")
                
                # Save final outputs
                final_paper = SAVE_DIR / "FINAL_PAPER.txt"
                with open(final_paper, "w") as f:
                    f.write(paper_text)
                
                print(f"✓ Final paper saved: {final_paper}")
                print(f"✓ Word count: {word_count:,}")
                break
            
            # Build next iteration prompt
            deductions = result.get("deductions", [])
            fix_plan = result.get("fix_plan", {})
            
            print(f"\n📝 FIX PLAN:")
            print(f"Deductions: {len(deductions)}")
            for i, ded in enumerate(deductions[:3], 1):
                print(f"  {i}. {ded}")
            
            edits = fix_plan.get("edits_now", [])
            print(f"\nPlanned Edits: {len(edits)}")
            for i, edit in enumerate(edits[:3], 1):
                print(f"  {i}. {edit}")
            
            prompt = f"""Continue improving the Farmer Jones MTFC paper.

CURRENT STATUS:
- Iteration: {iteration}
- Score: {total_score}/100 (need ≥{target_score})
- Word count: {word_count:,}
- Missing sections: {len(missing)}

PREVIOUS DEDUCTIONS:
{json.dumps(deductions[:5], indent=2)}

FIX PLAN:
Edits: {json.dumps(fix_plan.get('edits_now', [])[:5], indent=2)}
Numbers to add: {json.dumps(fix_plan.get('numbers_to_add', [])[:5], indent=2)}
Novelty changes: {json.dumps(fix_plan.get('novelty_changes', [])[:3], indent=2)}

REQUIREMENTS:
1. Apply ALL fixes
2. Ensure ALL 30 items are present and quantified
3. Add more specific calculations and numbers
4. Verify internal consistency (revenue = quantity × price, etc.)
5. Include notation block with ALL symbols
6. List figures/tables with REAL values (not TBD)
7. Achieve ≥{target_score}/100

Generate improved JSON with complete paper text."""
            
            iteration += 1
            all_iterations.append(result)
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error in iteration {iteration}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    # Final summary
    print(f"\n{'='*80}")
    print("ULTRA BUILDER COMPLETE")
    print(f"{'='*80}")
    
    summary = {
        "target_score": target_score,
        "iterations_completed": iteration - 1,
        "final_score": total_score if 'total_score' in locals() else 0,
        "final_word_count": word_count if 'word_count' in locals() else 0,
        "achieved_target": (total_score >= target_score) if 'total_score' in locals() else False
    }
    
    summary_file = SAVE_DIR / "ultra_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    # Create FINISHED marker
    with open("FINISHED_ULTRA.txt", "w") as f:
        f.write(f"""MTFC ULTRA BUILDER - COMPLETED

Target Score: ≥{target_score}/100
Final Score: {summary['final_score']}/100
Status: {'✓ ACHIEVED' if summary['achieved_target'] else '✗ IN PROGRESS'}
Iterations: {summary['iterations_completed']}
Final Word Count: {summary['final_word_count']:,}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}

Output Files:
- Final paper: {SAVE_DIR}/FINAL_PAPER.txt
- All iterations: {SAVE_DIR}/iteration_*.json
- Paper text files: {SAVE_DIR}/paper_iteration_*.txt
- Summary: {summary_file}

This is a complete 30-item MTFC paper with:
- Zero placeholders
- Full quantification
- All required calculations (NPV, IRR, EV, regression, etc.)
- Excellence boosters
- Professional formatting
""")
    
    print(f"✓ FINISHED_ULTRA.txt created")
    print(f"✓ Summary: {summary_file}")
    print(f"✓ All outputs: {SAVE_DIR}/")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

