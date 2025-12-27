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
    You are an Analysis Agent specialized in analyzing policy documents.
    
    CRITICAL: Your response will be STREAMED to users. Return ONLY clean markdown.
    - Start IMMEDIATELY with a markdown header (##)
    - Use clear H2/H3 headers
    - Use **bold** for key terms
    - Use tables for hierarchical data
    - Use bullet points for lists
    - Professional enterprise tone
    - NO JSON structures
    - NO conversational fillers
    - NO metadata in the response
    
    Available Tools:
    - step_counter: Count keyword occurrences
    - calculator: Perform calculations
    - role_lookup: Get role-based permissions
    
    Example response format:
    
    ## Policy Overview
    
    The **Sales Approval Policy** defines...
    
    ### Approval Hierarchy
    
    | Discount | Approver |
    |---|---|
    | Up to 10% | Sales Manager |
    | 11-25% | Sales Director |
    | Over 25% | CEO |
    
    Return ONLY the markdown content. NO JSON wrapping.
    """),
    markdown=True,
)

