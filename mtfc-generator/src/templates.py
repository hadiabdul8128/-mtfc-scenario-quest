"""Template system for MTFC report generation"""

from typing import Dict, Any
from .utils import load_config


class ReportTemplate:
    """Template manager for MTFC reports."""
    
    def __init__(self):
        self.prompts = load_config("prompts")
        self.generation_prompts = self.prompts["generation"]
    
    def get_step_prompt(self, step: int, context: Dict[str, Any]) -> str:
        """Get the prompt for a specific step."""
        step_keys = {
            1: "step_1_project_definition",
            2: "step_2_data_identification",
            3: "step_3_mathematical_modeling",
            4: "step_4_risk_analysis",
            5: "step_5_recommendations"
        }
        
        if step not in step_keys:
            raise ValueError(f"Invalid step number: {step}. Must be 1-5.")
        
        step_key = step_keys[step]
        prompt_template = self.generation_prompts[step_key]["prompt"]
        
        # Extract format keys from the template and ensure all are provided
        import string
        formatter = string.Formatter()
        format_keys = [field_name for _, field_name, _, _ in formatter.parse(prompt_template) if field_name]
        
        # Build safe context with defaults for missing keys
        safe_context = {}
        for key in format_keys:
            safe_context[key] = context.get(key, "")
        
        return prompt_template.format(**safe_context)
    
    def format_full_report(self, steps: Dict[int, str], scenario_name: str) -> str:
        """Format the complete report from individual steps."""
        report_parts = [
            f"# MTFC Actuarial Analysis Report",
            f"",
            f"## Scenario: {scenario_name}",
            f"",
            steps.get(1, ""),
            steps.get(2, ""),
            steps.get(3, ""),
            steps.get(4, ""),
            steps.get(5, ""),
            f"",
            f"---",
            f"",
            f"*Generated using the 5-Step Actuarial Process*"
        ]
        return "\n".join(report_parts)

