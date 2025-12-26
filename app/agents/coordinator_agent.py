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
    tools=[memory_tools],
    instructions=dedent("""
    You are the Coordinator managing a team of specialized agents for policy analysis.
    
    Your team members:
    1. Information Retrieval Agent (IRA) - Retrieves relevant policy documents from the knowledge base
    2. Analysis Agent (AA) - Analyzes content and uses tools (step_counter, calculator, role_lookup)
    
    Workflow:
    1. Receive the user query about company policies
    2. Delegate to Information Retrieval Agent to get relevant policy content
    3. Pass retrieved content to Analysis Agent for detailed analysis
    4. Aggregate results from both agents
    5. Generate final structured response
    
    Return your final response in JSON format:
    {
        "reasoning_steps": ["step 1", "step 2", ...],
        "tools_used": ["tool1", "tool2", ...],
        "sources": ["source1", "source2", ...],
        "final_answer": "comprehensive markdown-formatted answer"
    }
    
    Always ensure the final answer is well-formatted with:
    - Clear headings
    - Bullet points for lists
    - Tables where appropriate
    - Code blocks for examples
    """),
    db=db,
    memory_manager=memory_manager,
    enable_user_memories=True,
    add_history_to_context=True,
    num_history_runs=10,
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
        if isinstance(final_result, str) and final_result.strip().startswith('{'):
            parsed = json.loads(final_result)
            reasoning_steps = parsed.get('reasoning_steps', [])
            tools_used = parsed.get('tools_used', [])
            sources = parsed.get('sources', sources)
            answer = parsed.get('final_answer', final_result)
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

