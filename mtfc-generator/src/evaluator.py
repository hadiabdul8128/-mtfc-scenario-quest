"""Rubric evaluator module for MTFC reports"""

import json
import re
from typing import Dict, Any, Optional
from openai import OpenAI
from anthropic import Anthropic
from .utils import load_config, get_api_key


class RubricEvaluator:
    """Evaluates MTFC reports using a structured rubric."""
    
    def __init__(self, model: str = "gpt-4", provider: str = "openai"):
        """
        Initialize the evaluator.
        
        Args:
            model: Model name to use
            provider: LLM provider ("openai" or "anthropic")
        """
        self.model = model
        self.provider = provider
        self.rubric_config = load_config("rubric")
        self.prompts = load_config("prompts")
        self.weights = self.rubric_config["weights"]
        
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
                temperature=0.3,  # Lower temperature for more consistent evaluation
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        
        elif self.provider == "anthropic":
            system = system_prompt or ""
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response, handling markdown code blocks."""
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
                # Fallback: try to parse the whole response
                json_str = response
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract score manually
            score_match = re.search(r'"score":\s*(\d+)', response)
            justification_match = re.search(r'"justification":\s*"([^"]+)"', response)
            improvements_match = re.search(r'"improvements":\s*"([^"]+)"', response)
            
            return {
                "score": int(score_match.group(1)) if score_match else 0,
                "justification": justification_match.group(1) if justification_match else "Failed to parse response",
                "improvements": improvements_match.group(1) if improvements_match else "No improvements suggested"
            }
    
    def evaluate_category(self, category: str, report_text: str) -> Dict[str, Any]:
        """
        Evaluate a specific rubric category.
        
        Args:
            category: Category name (e.g., "project_definition")
            report_text: Full report text to evaluate
        
        Returns:
            Dictionary with score, justification, and improvements
        """
        if category not in self.prompts["evaluation"]:
            raise ValueError(f"Unknown category: {category}")
        
        category_prompt_config = self.prompts["evaluation"][category]
        prompt = category_prompt_config["prompt"].format(report_text=report_text)
        system_prompt = self.prompts["evaluation"]["system_prompt"]
        
        response = self._call_llm(prompt, system_prompt)
        result = self._extract_json_from_response(response)
        
        # Ensure score is within valid range
        score = max(0, min(100, result.get("score", 0)))
        result["score"] = score
        
        return result
    
    def evaluate_report(self, report_text: str) -> Dict[str, Any]:
        """
        Evaluate a complete report using all rubric categories.
        
        Args:
            report_text: Full report text to evaluate
        
        Returns:
            Dictionary with scores for each category, weighted total, and feedback
        """
        categories = list(self.weights.keys())
        scores = {}
        feedback = {}
        
        print("Evaluating report...")
        for category in categories:
            print(f"  Evaluating {category}...")
            result = self.evaluate_category(category, report_text)
            scores[category] = result["score"]
            feedback[category] = {
                "score": result["score"],
                "justification": result.get("justification", ""),
                "improvements": result.get("improvements", "")
            }
        
        # Calculate weighted total
        weighted_total = sum(
            scores[category] * self.weights[category]
            for category in categories
        )
        
        return {
            "scores": scores,
            "weighted_total": weighted_total,
            "feedback": feedback,
            "target_score": self.rubric_config["target_score"],
            "passed": weighted_total >= self.rubric_config["target_score"]
        }
    
    def get_categories_below_threshold(self, evaluation_result: Dict[str, Any], 
                                      threshold: int = 90) -> list:
        """
        Get list of categories that scored below the threshold.
        
        Args:
            evaluation_result: Result from evaluate_report()
            threshold: Score threshold (default: 90)
        
        Returns:
            List of category names below threshold
        """
        below_threshold = []
        for category, score in evaluation_result["scores"].items():
            if score < threshold:
                below_threshold.append(category)
        return below_threshold
    
    def get_improvement_summary(self, evaluation_result: Dict[str, Any]) -> str:
        """
        Generate a summary of improvements needed.
        
        Args:
            evaluation_result: Result from evaluate_report()
        
        Returns:
            Formatted string with improvement suggestions
        """
        feedback = evaluation_result["feedback"]
        summary_parts = []
        
        for category, info in feedback.items():
            if info["score"] < 90:
                summary_parts.append(
                    f"{category.upper()} (Score: {info['score']}/100):\n"
                    f"  {info['improvements']}\n"
                )
        
        return "\n".join(summary_parts)

