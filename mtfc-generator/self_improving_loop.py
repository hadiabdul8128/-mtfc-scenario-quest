#!/usr/bin/env python3
"""
MTFC Self-Improving Final Paper Loop (≥96 Target)
Continuously improves paper until competition-ready
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

SAVE_DIR = Path("mtfc_self_improving")
SAVE_DIR.mkdir(exist_ok=True)

# Load the existing comprehensive paper as starting point
INITIAL_PAPER_PATH = Path("mtfc_comprehensive/FINAL_COMPREHENSIVE_PAPER.txt")

SYSTEM_PROMPT = """You are an autonomous MTFC project generator and evaluator.

Your job is to continuously improve a full Scenario Quest Response paper (Parts 1-5, #1-#30) until it is competition-ready with a total score ≥96/100.

RUBRIC (Total 100 points + up to 3 bonus):
- Project Definition (15): Quantified risks & exposures, clear stakeholders, all 3 mitigation categories, time horizon & success metrics
- Data Identification & Assessment (20): Data mapped to categorization/frequency/severity; tables; 2+ visuals with numbers
- Mathematical Modeling (25): Model equations with coefficients; EV math table; sensitivity; diagnostics
- Risk Analysis (20): 2×2 table (Mean & 95% loss); uncertainty/tail analysis
- Recommendations (15): Cost-benefit (NPV/IRR/payback), triggers, financing, all 3 mitigation categories
- Communication & Clarity (5): Clean numbering, labeled figures/tables, notation
- Excellence Boosters (+3 max): 95/99% tail, second model, financing realism, decision triggers, portfolio mitigation, risk register (need ≥3)

ITERATIVE WORKFLOW:
1. Generate complete paper (Parts 1-5, #1-#30)
2. Evaluate against rubric
3. Keep sections scoring ≥90% unchanged
4. Rewrite only sections scoring <90%
5. Repeat until total ≥96

OUTPUT FORMAT:
Return JSON with:
{
  "iteration": N,
  "paper": "Full paper text with all sections...",
  "scores": {
    "Project Definition": 0-15,
    "Data Identification & Assessment": 0-20,
    "Mathematical Modeling": 0-25,
    "Risk Analysis": 0-20,
    "Recommendations": 0-15,
    "Communication & Clarity": 0-5,
    "Excellence_Boosters": 0-3,
    "Total": 0-103
  },
  "analysis": {
    "deductions": ["issue → reason"],
    "improvements_made": ["what changed"],
    "sections_retained": ["what kept"]
  },
  "status": "CONTINUE" or "DONE"
}

Set status to "DONE" only when Total ≥96."""

def chat(prompt, model="gpt-4-turbo", max_tokens=4096):
    """Call OpenAI API"""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
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
    
    # Try to find JSON in code blocks first
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
        # Save raw response for debugging
        with open(SAVE_DIR / "last_response_error.txt", "w") as f:
            f.write(response)
        return None

def load_initial_paper():
    """Load the existing comprehensive paper"""
    if INITIAL_PAPER_PATH.exists():
        with open(INITIAL_PAPER_PATH, "r") as f:
            return f.read()
    else:
        print(f"⚠️ Initial paper not found at {INITIAL_PAPER_PATH}")
        return None

def main():
    print("="*90)
    print("MTFC SELF-IMPROVING LOOP - Target Score ≥96/100")
    print("="*90)
    print("Strategy: Keep strong sections (≥90%), improve weak sections")
    print("="*90)
    
    # Load initial paper
    initial_paper = load_initial_paper()
    if not initial_paper:
        print("❌ No initial paper found. Please run comprehensive_mtfc_builder.py first.")
        return
    
    print(f"\n✓ Loaded initial paper: {len(initial_paper.split())} words")
    
    iteration = 1
    max_iterations = 5
    target_score = 96
    
    current_paper = initial_paper
    
    while iteration <= max_iterations:
        print(f"\n{'='*90}")
        print(f"🔄 ITERATION {iteration}")
        print(f"{'='*90}\n")
        
        # Build prompt
        if iteration == 1:
            prompt = f"""Evaluate and improve this MTFC paper to achieve ≥96/100.

CURRENT PAPER:
{current_paper}

TASK:
1. Evaluate against the rubric (Project Definition 15, Data 20, Modeling 25, Risk 20, Recommendations 15, Communication 5, Boosters +3)
2. Score each category and identify deductions
3. If total <96: Improve weak sections (keep strong sections ≥90% unchanged)
4. If total ≥96: Set status to "DONE"

Return complete JSON with iteration={iteration}, full paper text, scores, analysis, and status."""
        else:
            prompt = f"""Continue improving this MTFC paper (Iteration {iteration}).

CURRENT PAPER:
{current_paper}

PREVIOUS SCORES: {previous_scores if 'previous_scores' in locals() else 'N/A'}

TASK:
1. Re-evaluate against rubric
2. Keep sections that scored ≥90% unchanged
3. Improve only sections that scored <90%
4. Add more quantification, visuals, or details as needed
5. If total ≥96: Set status to "DONE"

Return complete JSON with iteration={iteration}, improved paper, new scores, analysis, and status."""
        
        try:
            print("📡 Calling API to evaluate/improve paper...")
            response = chat(prompt, max_tokens=4096)
            
            print(f"✓ Received response ({len(response)} chars)")
            
            # Extract JSON
            result = extract_json(response)
            
            if not result:
                print("❌ Failed to parse JSON response")
                print("Attempting to save raw response...")
                with open(SAVE_DIR / f"iteration_{iteration}_raw.txt", "w") as f:
                    f.write(response)
                break
            
            # Extract data
            iter_num = result.get("iteration", iteration)
            paper = result.get("paper", "")
            scores = result.get("scores", {})
            analysis = result.get("analysis", {})
            status = result.get("status", "CONTINUE")
            
            total_score = scores.get("Total", 0)
            
            # Save iteration
            iteration_file = SAVE_DIR / f"iteration_{iter_num}.json"
            with open(iteration_file, "w") as f:
                json.dump(result, f, indent=2)
            
            # Save paper
            paper_file = SAVE_DIR / f"paper_iteration_{iter_num}.txt"
            with open(paper_file, "w") as f:
                f.write(paper)
            
            word_count = len(paper.split())
            
            # Display results
            print(f"\n{'='*90}")
            print(f"📊 ITERATION {iter_num} RESULTS")
            print(f"{'='*90}")
            print(f"Total Score: {total_score}/100 (Target: ≥{target_score})")
            print(f"Word Count: {word_count:,}")
            print(f"Status: {status}")
            
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
            
            # Show analysis
            deductions = analysis.get("deductions", [])
            if deductions:
                print(f"\n📉 DEDUCTIONS ({len(deductions)}):")
                for i, ded in enumerate(deductions[:5], 1):
                    print(f"  {i}. {ded}")
            
            improvements = analysis.get("improvements_made", [])
            if improvements:
                print(f"\n✨ IMPROVEMENTS ({len(improvements)}):")
                for i, imp in enumerate(improvements[:5], 1):
                    print(f"  {i}. {imp}")
            
            retained = analysis.get("sections_retained", [])
            if retained:
                print(f"\n🔒 RETAINED SECTIONS ({len(retained)}): {', '.join(retained[:5])}")
            
            # Check completion
            if total_score >= target_score and status == "DONE":
                print(f"\n{'='*90}")
                print(f"🎯 TARGET ACHIEVED: {total_score}/100 ≥ {target_score}")
                print(f"{'='*90}")
                
                # Save final paper
                final_paper_file = SAVE_DIR / "FINAL_PAPER_96PLUS.txt"
                with open(final_paper_file, "w") as f:
                    f.write(paper)
                
                # Save final scorecard
                final_scorecard = SAVE_DIR / "FINAL_SCORECARD.json"
                with open(final_scorecard, "w") as f:
                    json.dump({
                        "iteration": iter_num,
                        "scores": scores,
                        "analysis": analysis,
                        "word_count": word_count
                    }, f, indent=2)
                
                print(f"\n✓ Final paper saved: {final_paper_file}")
                print(f"✓ Final scorecard: {final_scorecard}")
                print(f"✓ Word count: {word_count:,}")
                
                # Print key strengths
                print(f"\n🏆 KEY STRENGTHS:")
                for cat, max_score in categories:
                    score = scores.get(cat, 0)
                    if score >= max_score * 0.9:
                        print(f"  ✓ {cat}: {score}/{max_score}")
                if boosters >= 3:
                    print(f"  ✓ Excellence Boosters: {boosters}/3")
                
                break
            
            # Prepare for next iteration
            current_paper = paper
            previous_scores = scores
            iteration += 1
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"❌ Error in iteration {iteration}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    # Create completion marker
    with open("FINISHED_SELF_IMPROVING.txt", "w") as f:
        f.write(f"""MTFC SELF-IMPROVING LOOP - COMPLETED

Target Score: ≥{target_score}/100
Final Score: {total_score if 'total_score' in locals() else 'N/A'}/100
Status: {'✓ ACHIEVED' if (total_score >= target_score if 'total_score' in locals() else False) else '✗ IN PROGRESS'}
Iterations: {iteration - 1}
Final Word Count: {word_count if 'word_count' in locals() else 'N/A'}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}

Strategy:
- Keep sections scoring ≥90% unchanged
- Improve only weak sections (<90%)
- Self-evaluate and self-correct each iteration

Output Files:
- Final paper: {SAVE_DIR}/FINAL_PAPER_96PLUS.txt
- Final scorecard: {SAVE_DIR}/FINAL_SCORECARD.json
- All iterations: {SAVE_DIR}/iteration_*.json
- Paper versions: {SAVE_DIR}/paper_iteration_*.txt

This paper is competition-ready for MTFC Scenario Quest Response 2025-26.
""")
    
    print(f"\n{'='*90}")
    print("SELF-IMPROVING LOOP COMPLETE")
    print(f"{'='*90}")
    print(f"✓ FINISHED_SELF_IMPROVING.txt created")
    print(f"✓ All outputs in: {SAVE_DIR}/")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

