"""Iterative improvement engine for MTFC reports"""

import json
from typing import Dict, Any, List
from .generator import ScriptGenerator
from .evaluator import RubricEvaluator
from .utils import load_config


class ImprovementEngine:
    """Iteratively improves MTFC reports until all criteria meet the threshold."""
    
    def __init__(self, model: str = "gpt-4", provider: str = "openai"):
        """
        Initialize the improvement engine.
        
        Args:
            model: Model name to use
            provider: LLM provider ("openai" or "anthropic")
        """
        self.generator = ScriptGenerator(model=model, provider=provider)
        self.evaluator = RubricEvaluator(model=model, provider=provider)
        self.rubric_config = load_config("rubric")
        self.target_score = self.rubric_config["target_score"]
        self.max_iterations = self.rubric_config["max_iterations"]
        
        self.iteration_history: List[Dict[str, Any]] = []
    
    def improve_until_threshold(self, initial_report: str, 
                               scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Iteratively improve a report until all categories score ≥ threshold.
        
        Args:
            initial_report: Initial report text
            scenario_data: Scenario data for context
        
        Returns:
            Dictionary with final report, scores, and iteration history
        """
        current_report = initial_report
        iteration = 0
        
        print(f"Starting iterative improvement (target: {self.target_score}, max iterations: {self.max_iterations})...")
        
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"Iteration {iteration}")
            print(f"{'='*60}")
            
            # Evaluate current report
            evaluation = self.evaluator.evaluate_report(current_report)
            
            # Store iteration history
            iteration_data = {
                "iteration": iteration,
                "scores": evaluation["scores"].copy(),
                "weighted_total": evaluation["weighted_total"],
                "feedback": evaluation["feedback"].copy()
            }
            self.iteration_history.append(iteration_data)
            
            # Print current scores
            print(f"\nCurrent Scores:")
            for category, score in evaluation["scores"].items():
                status = "✓" if score >= self.target_score else "✗"
                print(f"  {status} {category}: {score}/100")
            print(f"\nWeighted Total: {evaluation['weighted_total']:.2f}/100")
            
            # Check if all categories meet threshold
            categories_below = self.evaluator.get_categories_below_threshold(
                evaluation, self.target_score
            )
            
            if not categories_below:
                print(f"\n✓ All categories meet threshold ({self.target_score})!")
                break
            
            print(f"\nCategories below threshold: {', '.join(categories_below)}")
            
            # Improve the report
            print("\nImproving report...")
            current_report = self.generator.improve_report(
                current_report, 
                evaluation["feedback"]
            )
        
        # Final evaluation
        final_evaluation = self.evaluator.evaluate_report(current_report)
        
        return {
            "final_report": current_report,
            "final_scores": final_evaluation["scores"],
            "final_weighted_total": final_evaluation["weighted_total"],
            "iteration_history": self.iteration_history,
            "total_iterations": iteration,
            "converged": iteration < self.max_iterations,
            "passed": final_evaluation["weighted_total"] >= self.target_score
        }
    
    def generate_and_improve(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an initial report and iteratively improve it.
        
        Args:
            scenario_data: Dictionary containing scenario information
        
        Returns:
            Dictionary with final report, scores, and iteration history
        """
        print("Generating initial report...")
        initial_report = self.generator.generate_full_report(scenario_data)
        
        print("\nInitial report generated. Starting improvement process...")
        result = self.improve_until_threshold(initial_report, scenario_data)
        
        return result
    
    def get_improvement_summary(self) -> str:
        """Get a summary of the improvement process."""
        if not self.iteration_history:
            return "No iterations completed."
        
        summary_parts = [
            f"Total Iterations: {len(self.iteration_history)}",
            f"Final Weighted Score: {self.iteration_history[-1]['weighted_total']:.2f}/100",
            "\nIteration History:"
        ]
        
        for i, iteration in enumerate(self.iteration_history, 1):
            summary_parts.append(f"\nIteration {i}:")
            summary_parts.append(f"  Weighted Total: {iteration['weighted_total']:.2f}/100")
            for category, score in iteration["scores"].items():
                summary_parts.append(f"  {category}: {score}/100")
        
        return "\n".join(summary_parts)
    
    def save_iteration_history(self, filepath: str):
        """Save iteration history to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.iteration_history, f, indent=2)

