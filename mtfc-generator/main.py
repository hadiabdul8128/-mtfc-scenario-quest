#!/usr/bin/env python3
"""CLI interface for MTFC Script Generator and Evaluator"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from src.improver import ImprovementEngine
from src.generator import ScriptGenerator
from src.evaluator import RubricEvaluator
from src.utils import save_output, load_config


def create_sample_scenario(name: str = "Smith County Corn Farming") -> Dict[str, Any]:
    """Create a sample scenario for testing."""
    return {
        "name": name,
        "description": f"""
        Risk: Corn yield volatility due to drought in {name.split()[0]} County, Iowa.
        
        Who is at Risk: Independent farmers, insurance carriers, and local food distributors.
        
        Possible Mitigation: Irrigation installation, soil moisture sensors, and yield insurance.
        """,
        "data_sources": """
        - FCIC Cause of Loss dataset (1994-2024)
        - Corn Planting Costs (2016-2025)
        - Corn Harvest Prices
        - Historical weather data
        """,
        "data_summary": """
        - Frequency: Drought claims occurred in 12 of 30 years (40% frequency)
        - Severity: Average loss per acre = $425
        - Price volatility: Historical price range $3.50-$7.00 per bushel
        """,
        "model_results": "",
        "risk_analysis": ""
    }


def load_scenario_from_file(filepath: str) -> Dict[str, Any]:
    """Load scenario data from a JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def save_report_markdown(report: str, output_dir: str, filename: str = None):
    """Save report as markdown."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mtfc_report_{timestamp}.md"
    
    filepath = save_output(report, filename, output_dir)
    print(f"Report saved to: {filepath}")
    return filepath


def save_report_json(result: Dict[str, Any], output_dir: str, filename: str = None):
    """Save results as JSON."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mtfc_results_{timestamp}.json"
    
    output_path = Path(__file__).parent / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    filepath = output_path / filename
    
    with open(filepath, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Results saved to: {filepath}")
    return str(filepath)


def export_to_pdf(report: str, output_dir: str, filename: str = None):
    """Export report to PDF (requires reportlab)."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        import markdown
    except ImportError:
        print("Warning: reportlab or markdown not installed. PDF export disabled.")
        print("Install with: pip install reportlab markdown")
        return None
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mtfc_report_{timestamp}.pdf"
    
    output_path = Path(__file__).parent / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    filepath = output_path / filename
    
    # Convert markdown to HTML then to PDF
    html = markdown.markdown(report)
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Simple text extraction for PDF (basic implementation)
    for line in report.split('\n'):
        if line.strip():
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                style_name = f'Heading{min(level, 6)}'
                story.append(Paragraph(line.lstrip('# '), styles[style_name]))
            else:
                story.append(Paragraph(line, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
    
    doc.build(story)
    print(f"PDF saved to: {filepath}")
    return str(filepath)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MTFC Script Generator and Evaluator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report for sample scenario
  python main.py --scenario "Smith County Corn Farming"
  
  # Load scenario from file
  python main.py --scenario-file data/scenarios/corn_farming.json
  
  # Specify output format
  python main.py --scenario "Test Scenario" --output-format markdown pdf json
  
  # Use different model
  python main.py --scenario "Test" --model gpt-4-turbo --provider openai
        """
    )
    
    parser.add_argument(
        "--scenario",
        type=str,
        help="Scenario name (will use sample scenario if scenario-file not provided)"
    )
    
    parser.add_argument(
        "--scenario-file",
        type=str,
        help="Path to JSON file containing scenario data"
    )
    
    parser.add_argument(
        "--output-format",
        nargs="+",
        choices=["markdown", "json", "pdf"],
        default=["markdown", "json"],
        help="Output formats (default: markdown json)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/reports",
        help="Output directory (default: output/reports)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4",
        help="LLM model to use (default: gpt-4)"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM provider (default: openai)"
    )
    
    parser.add_argument(
        "--no-improvement",
        action="store_true",
        help="Generate report without iterative improvement"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        help="Maximum number of improvement iterations (overrides config)"
    )
    
    args = parser.parse_args()
    
    # Load scenario data
    if args.scenario_file:
        scenario_data = load_scenario_from_file(args.scenario_file)
    elif args.scenario:
        scenario_data = create_sample_scenario(args.scenario)
    else:
        scenario_data = create_sample_scenario()
        print("No scenario specified. Using sample scenario: Smith County Corn Farming")
    
    # Initialize engine
    engine = ImprovementEngine(model=args.model, provider=args.provider)
    
    if args.max_iterations:
        engine.max_iterations = args.max_iterations
    
    # Generate and improve report
    try:
        if args.no_improvement:
            print("Generating report without iterative improvement...")
            generator = ScriptGenerator(model=args.model, provider=args.provider)
            report = generator.generate_full_report(scenario_data)
            
            evaluator = RubricEvaluator(model=args.model, provider=args.provider)
            evaluation = evaluator.evaluate_report(report)
            
            result = {
                "final_report": report,
                "final_scores": evaluation["scores"],
                "final_weighted_total": evaluation["weighted_total"],
                "iteration_history": [],
                "total_iterations": 0,
                "converged": False,
                "passed": evaluation["weighted_total"] >= engine.target_score
            }
        else:
            result = engine.generate_and_improve(scenario_data)
        
        # Print summary
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        print(f"\nFinal Weighted Score: {result['final_weighted_total']:.2f}/100")
        print(f"Target Score: {engine.target_score}")
        print(f"Status: {'PASSED' if result['passed'] else 'FAILED'}")
        print(f"Total Iterations: {result['total_iterations']}")
        print(f"\nFinal Category Scores:")
        for category, score in result['final_scores'].items():
            status = "✓" if score >= engine.target_score else "✗"
            print(f"  {status} {category}: {score}/100")
        
        # Save outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if "markdown" in args.output_format:
            save_report_markdown(
                result["final_report"],
                args.output_dir,
                f"mtfc_report_{timestamp}.md"
            )
        
        if "json" in args.output_format:
            save_report_json(
                result,
                args.output_dir,
                f"mtfc_results_{timestamp}.json"
            )
        
        if "pdf" in args.output_format:
            export_to_pdf(
                result["final_report"],
                args.output_dir,
                f"mtfc_report_{timestamp}.pdf"
            )
        
        print("\n✓ Process completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

