"""
Analysis Agent (AA)
Analyzes retrieved content and uses tools to generate answers
"""
import os
from dotenv import load_dotenv
from textwrap import dedent

from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools

from app.tools.policy_tools import PolicyTools

load_dotenv()

# Get environment variables
LLM_MODEL_API_KEY = os.getenv("LLM_MODEL_API_KEY")
LLM_MODEL_BASE_URL = os.getenv("LLM_MODEL_BASE_URL")

os.environ["OPENAI_API_KEY"] = LLM_MODEL_API_KEY

policy_tools = PolicyTools()
calculator_tools = CalculatorTools()

analysis_agent = Agent(
    name="Analysis Agent",
    model=OpenAIChat(
        id="gpt-4o-mini",
        api_key=LLM_MODEL_API_KEY,
        base_url=LLM_MODEL_BASE_URL,
    ),
    tools=[policy_tools, calculator_tools],
    description="Analyzes policy content and uses tools to generate comprehensive answers.",
    instructions=dedent("""
    You are an Analysis Agent specialized in analyzing policy documents and generating insights.
    
    Available Tools:
    - step_counter: Count occurrences of keywords in text
    - calculator: Perform arithmetic calculations
    - role_lookup: Get role-based permissions and approval limits
    
    Your task:
    1. Analyze the retrieved policy content provided to you
    2. Use tools when needed (e.g., count steps, calculate totals, lookup roles)
    3. Generate a comprehensive, well-formatted answer
    4. Track your reasoning steps
    
    Return your analysis in JSON format:
    {
        "reasoning_steps": ["step 1", "step 2", ...],
        "tools_used": ["tool1", "tool2", ...],
        "analysis": "detailed analysis in markdown format",
        "key_findings": ["finding 1", "finding 2", ...]
    }
    """),
    markdown=True,
)

