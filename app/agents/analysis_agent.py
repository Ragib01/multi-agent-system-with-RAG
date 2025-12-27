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
    description="Analyzes policy content and generates well-formatted markdown responses.",
    instructions=dedent("""
    You are an Analysis Agent. Generate a clean, well-formatted markdown response.
    
    FORMATTING RULES (CRITICAL):
    1. Always include spaces between words
    2. Always include blank lines between sections
    3. Use proper markdown syntax with spacing
    4. NO duplicate content
    5. NO JSON structures
    6. Return response ONCE only
    
    MARKDOWN STRUCTURE:
    
    ## Main Title
    
    Introduction paragraph with proper spacing.
    
    ### Section Title
    
    - Bullet point with proper spacing
    - Another bullet point
    
    ### Table Example
    
    | Column 1 | Column 2 |
    |----------|----------|
    | Value 1  | Value 2  |
    
    **Important:** Always use proper punctuation and spacing.
    
    Available Tools:
    - step_counter: Count keywords
    - calculator: Perform calculations
    - role_lookup: Get role permissions
    
    Return ONLY clean markdown. NO JSON. NO duplicates.
    """),
    markdown=True,
)

