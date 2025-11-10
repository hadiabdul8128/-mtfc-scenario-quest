"""Utility functions for MTFC Generator"""

import json
import os
from typing import Dict, Any
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip


def load_config(config_name: str) -> Dict[str, Any]:
    """Load a configuration file from the config directory."""
    config_path = Path(__file__).parent.parent / "config" / f"{config_name}.json"
    with open(config_path, "r") as f:
        return json.load(f)


def get_api_key() -> str:
    """Get API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable."
        )
    return api_key


def save_output(content: str, filename: str, output_dir: str = "output/reports") -> str:
    """Save output to a file."""
    output_path = Path(__file__).parent.parent / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / filename
    with open(file_path, "w") as f:
        f.write(content)
    return str(file_path)


def format_section(title: str, content: str, level: int = 1) -> str:
    """Format a report section with proper markdown headers."""
    prefix = "#" * level
    return f"{prefix} {title}\n\n{content}\n\n"

