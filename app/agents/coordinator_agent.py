"""
Coordinator Agent
Orchestrates the multi-agent workflow: receives query, routes to worker agents, aggregates results
"""
import os
import json
from dotenv import load_dotenv
from textwrap import dedent
from typing import Dict, Any

from agno.team import Team
from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.postgres import PostgresDb
from agno.memory import MemoryManager
from agno.tools.memory import MemoryTools

from app.tools.policy_tools import PolicyTools
from app.agents.information_retrieval_agent import information_retrieval_agent
from app.agents.analysis_agent import analysis_agent

load_dotenv()

# Get environment variables
POSTGRES_DB_URL = os.getenv("POSTGRES_DB_URL")
LLM_MODEL_API_KEY = os.getenv("LLM_MODEL_API_KEY")
LLM_MODEL_BASE_URL = os.getenv("LLM_MODEL_BASE_URL")

os.environ["OPENAI_API_KEY"] = LLM_MODEL_API_KEY

db = PostgresDb(db_url=POSTGRES_DB_URL)

memory_tools = MemoryTools(db=db)

memory_manager = MemoryManager(
    db=db,
    model=OpenAIChat(
        id="gpt-4o-mini",
        base_url=LLM_MODEL_BASE_URL,
    ),
    memory_capture_instructions="Extract and store key information about the user including their name, preferences, personal details etc.",
)

coordinator_team = Team(
    name="Policy Analysis Team",
    members=[information_retrieval_agent, analysis_agent],
    model=OpenAIChat(
        id="gpt-4o-mini",
        api_key=LLM_MODEL_API_KEY,
        base_url=LLM_MODEL_BASE_URL,
        cache_response=True,
        cache_ttl=7200,
        cache_dir=".agno/cache/model_responses"
    ),
    tools=[PolicyTools],
    instructions=dedent("""
    You are the Coordinator managing a team for policy analysis.
    
    FORMATTING RULES (CRITICAL):
    1. Always include spaces between words
    2. Always include blank lines between sections (use double newlines)
    3. Use proper markdown syntax with spacing
    4. NO duplicate content - return response ONCE only
    5. NO JSON structures
    6. Professional executive tone
    
    MARKDOWN STRUCTURE:
    
    ## Main Policy Title
    
    Opening paragraph explaining the policy with proper spacing between words.
    
    ### Key Points
    
    - First bullet point with proper spacing
    - Second bullet point
    
    ### Approval Process
    
    | Level | Approver | Limit |
    |-------|----------|-------|
    | 1 | Manager | $5,000 |
    | 2 | Director | $25,000 |
    
    **Note:** Always use proper punctuation, spacing, and formatting.
    
    Team: IRA (retrieves docs) + AA (analyzes with tools)
    
    Return ONLY clean markdown. NO JSON. NO duplicates. Proper spacing required.
    """),
    markdown=True,
    debug_mode=True,
)


def run_multi_agent_query(query: str, session_id: str) -> Dict[str, Any]:
    """
    Run a query through the multi-agent team system
    
    Args:
        query: User's question about policies
        session_id: Session identifier for context management
        
    Returns:
        Dictionary with answer, sources, tools_used, and reasoning_steps
    """
    print(f"\n[Team] Processing query through multi-agent system...")
    print(f"[Team] Query: {query}")
    
    # Run the team - it will coordinate between IRA and AA automatically
    team_response = coordinator_team.run(
        input=query,
        session_id=session_id,
        stream=False,
    )
    
    final_result = team_response.content if hasattr(team_response, 'content') else str(team_response)
    print(f"[Team] Processing complete")
    
    # Parse the response
    reasoning_steps = []
    tools_used = []
    sources = ["Organization Policies & Processes Manual"]
    answer = final_result
    
    try:
        # Check if response is JSON
        if isinstance(final_result, str) and final_result.strip().startswith('{'):
            parsed = json.loads(final_result)
            reasoning_steps = parsed.get('reasoning_steps', [])
            tools_used = parsed.get('tools_used', [])
            sources = parsed.get('sources', sources)
            answer = parsed.get('final_answer', final_result)
        # If it's already markdown (not JSON), use it directly
        elif isinstance(final_result, str) and final_result.strip().startswith('#'):
            answer = final_result
            reasoning_steps = [
                "Information Retrieval Agent found relevant policy documents",
                "Analysis Agent analyzed content with available tools",
                "Coordinator generated comprehensive response"
            ]
            tools_used = ['information_retrieval', 'analysis', 'knowledge_search']
    except json.JSONDecodeError:
        reasoning_steps = [
            "Delegated query to Information Retrieval Agent",
            "Retrieved relevant policy documents",
            "Passed content to Analysis Agent",
            "Analysis Agent processed content and used tools",
            "Aggregated results into final response"
        ]
        tools_used = ['information_retrieval', 'analysis', 'knowledge_search']
    
    if not reasoning_steps:
        reasoning_steps = [
            "Received query and initiated multi-agent workflow",
            "Information Retrieval Agent searched knowledge base",
            "Analysis Agent analyzed retrieved content",
            "Coordinator aggregated results",
            "Generated comprehensive response"
        ]
    
    if not tools_used:
        tools_used = ['information_retrieval', 'analysis', 'knowledge_search']
    
    return {
        "answer": answer,
        "sources": sources,
        "tools_used": tools_used,
        "reasoning_steps": reasoning_steps
    }

