"""Script generator module for MTFC reports"""

import json
import os
from typing import Dict, Any, Optional
from openai import OpenAI
from anthropic import Anthropic
from .utils import load_config, get_api_key
from .templates import ReportTemplate


class ScriptGenerator:
    """Generates MTFC actuarial analysis reports using LLM."""
    
    def __init__(self, model: str = "gpt-4", provider: str = "openai"):
        """
        Initialize the generator.
        
        Args:
            model: Model name to use (e.g., "gpt-4", "gpt-4-turbo", "claude-3-opus")
            provider: LLM provider ("openai" or "anthropic")
        """
        self.model = model
        self.provider = provider
        self.template = ReportTemplate()
        self.prompts = load_config("prompts")
        
        # Initialize API client
        api_key = get_api_key()
        if provider == "openai":
            self.client = OpenAI(api_key=api_key)
        elif provider == "anthropic":
            self.client = Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Make an LLM API call."""
        if self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content.strip()
        
        elif self.provider == "anthropic":
            system = system_prompt or ""
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
    
    def generate_step(self, step: int, scenario_data: Dict[str, Any], 
                     previous_steps: Optional[Dict[int, str]] = None) -> str:
        """
        Generate a single step of the actuarial report.
        
        Args:
            step: Step number (1-5)
            scenario_data: Dictionary containing scenario information
            previous_steps: Dictionary of previously generated steps (for context)
        
        Returns:
            Generated step content as string
        """
        # Prepare context for the prompt
        context = {
            "scenario_description": scenario_data.get("description", ""),
            "scenario_name": scenario_data.get("name", "Unknown Scenario"),
            "data_sources": scenario_data.get("data_sources", "Not specified"),
            "data_summary": scenario_data.get("data_summary", ""),
            "model_results": scenario_data.get("model_results", ""),
            "risk_analysis": scenario_data.get("risk_analysis", "")
        }
        
        # Add context from previous steps if available
        if previous_steps:
            if step == 2 and 1 in previous_steps:
                context["project_definition"] = previous_steps[1]
            if step == 3 and 2 in previous_steps:
                context["data_summary"] = previous_steps[2]
            if step == 4 and 3 in previous_steps:
                context["model_results"] = previous_steps[3]
            if step == 5 and 4 in previous_steps:
                context["risk_analysis"] = previous_steps[4]
        
        # Get the prompt for this step
        prompt = self.template.get_step_prompt(step, context)
        system_prompt = self.prompts["generation"]["system_prompt"]
        
        # Generate the step
        content = self._call_llm(prompt, system_prompt)
        
        # Format as a numbered section
        step_names = {
            1: "Project Definition",
            2: "Data Identification & Assessment",
            3: "Mathematical Modeling",
            4: "Risk Analysis",
            5: "Recommendations"
        }
        
        return f"## {step}. {step_names[step]}\n\n{content}\n"
    
    def generate_full_report(self, scenario_data: Dict[str, Any]) -> str:
        """
        Generate a complete actuarial report following the 5-step process.
        
        Args:
            scenario_data: Dictionary containing scenario information
        
        Returns:
            Complete report as markdown string
        """
        steps = {}
        
        # Generate each step sequentially
        for step_num in range(1, 6):
            print(f"Generating Step {step_num}...")
            steps[step_num] = self.generate_step(step_num, scenario_data, steps)
        
        # Format the complete report
        report = self.template.format_full_report(steps, scenario_data.get("name", "Unknown Scenario"))
        
        return report
    
    def improve_report(self, current_report: str, feedback: Dict[str, Any]) -> str:
        """
        Improve an existing report based on evaluation feedback.
        
        Args:
            current_report: Current report text
            feedback: Dictionary containing scores and improvement suggestions
        
        Returns:
            Improved report as markdown string
        """
        improvement_prompt = self.prompts["improvement"]["prompt"]
        
        # Format scores and feedback
        scores_text = "\n".join([
            f"{cat}: {info.get('score', 'N/A')}/100 - {info.get('improvements', 'No feedback')}"
            for cat, info in feedback.items()
        ])
        
        prompt = improvement_prompt.format(
            scores_and_feedback=scores_text,
            current_report=current_report
        )
        
        system_prompt = self.prompts["generation"]["system_prompt"]
        improved_report = self._call_llm(prompt, system_prompt)
        
        return improved_report

