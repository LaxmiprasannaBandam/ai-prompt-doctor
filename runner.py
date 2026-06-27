"""
Prompt Doctor - Runner Module
Runs the student's prompt on the level's sample input using OpenRouter.
"""

import os
from pathlib import Path
from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv

# Load .env file from the project root directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_api_key() -> str:
    """Get API key from session state, .env, or secrets."""
    key = st.session_state.get("openrouter_api_key", "") or ""
    if not key.strip() or "your-openrouter" in key.lower() or key.strip() == "sk-or-v1-":
        key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key.strip() or "your-openrouter" in key.lower() or key.strip() == "sk-or-v1-":
        try:
            key = st.secrets.get("OPENROUTER_API_KEY", "")
        except Exception:
            key = ""
    return key


def run_student_prompt(student_prompt: str, sample_input: str) -> str:
    """
    Run the student's prompt on the sample input using OpenRouter.
    
    Args:
        student_prompt: The prompt written by the student
        sample_input: The sample input to test against
    
    Returns:
        str: The model's output
    """
    api_key = get_api_key()
    if not api_key.strip():
        return "ERROR: OpenRouter API key not found. Please set it in the sidebar or add OPENROUTER_API_KEY to your .env file."
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    model = os.environ.get("RUNNER_MODEL", "openai/gpt-4o-mini")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": student_prompt},
                {"role": "user", "content": sample_input}
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"ERROR running prompt: {str(e)}"
