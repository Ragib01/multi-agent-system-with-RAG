"""
RAG Agent with Memory Manager and Session Summaries
Note: JSON encoder patch must be applied in main.py before importing this module
"""
from re import L
from uuid import uuid4
import os
from dotenv import load_dotenv
from textwrap import dedent

from agno.agent.agent import Agent
from agno.memory import MemoryManager
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
from agno.session import SessionSummaryManager

from agno.tools.memory import MemoryTools
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector, SearchType
from agno.knowledge.embedder.openai import OpenAIEmbedder

from agno.models.openai import OpenAIChat

from app.tools.policy_tools import PolicyTools
from agno.tools.calculator import CalculatorTools
from agno.tools.reasoning import ReasoningTools

load_dotenv()

# Get environment variables
POSTGRES_DB_URL = os.getenv("POSTGRES_DB_URL")
LLM_MODEL_API_KEY = os.getenv("LLM_MODEL_API_KEY")
LLM_MODEL_BASE_URL = os.getenv("LLM_MODEL_BASE_URL")
RAG_AGENT_MODEL = os.getenv("RAG_AGENT_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

import os
os.environ["OPENAI_API_KEY"] = LLM_MODEL_API_KEY

# Check if all required environment variables are set
if not POSTGRES_DB_URL:
    raise ValueError("POSTGRES_DB_URL environment variable is required")

if not LLM_MODEL_API_KEY:
    raise ValueError("LLM_MODEL_API_KEY environment variable is required")

if not LLM_MODEL_BASE_URL:
    raise ValueError("LLM_MODEL_BASE_URL environment variable is required")

if not RAG_AGENT_MODEL:
    raise ValueError("RAG_AGENT_MODEL environment variable is required")


db_url = POSTGRES_DB_URL

db = PostgresDb(db_url=db_url)

memory_tools = MemoryTools(
    db=db,
)

policy_tools = PolicyTools()

# Memory Manager - automatically extracts and stores memories from conversations
memory_manager = MemoryManager(
    db=db,
    model=OpenAIChat(
        id="gpt-4o-mini", # small model for memory management
        base_url=LLM_MODEL_BASE_URL,
    ),
    memory_capture_instructions="Extract and store key information about the user including their name, preferences, personal details etc.",
)

# Setup your Session Summary Manager, to adjust how summaries are created
session_summary_manager = SessionSummaryManager(
    model=OpenAIChat(
        id="gpt-4o-mini", # small model for session summary management
        base_url=LLM_MODEL_BASE_URL,
    ),
    # You can also overwrite the prompt used for session summary creation
    session_summary_prompt="Create a very succinct summary of the following conversation:",
)

embedder = OpenAIEmbedder(
        id=EMBEDDING_MODEL,
        api_key=LLM_MODEL_API_KEY,
        base_url=LLM_MODEL_BASE_URL,
        dimensions=768
    )

knowledge = Knowledge(
    vector_db=PgVector(
            table_name="organization_policies_processes_vectors",
            db_url=POSTGRES_DB_URL,
            search_type=SearchType.hybrid, # SearchType.hybrid combines vector (semantic) and keyword (lexical) search for better results. 
            embedder=embedder,
        ),
    max_results=3,  # Get more context for comprehensive responses
)


openai_rag_agent = Agent(
    name="OpenAI RAG Agent",
    model=OpenAIChat(
        id="gpt-4o-mini",
        api_key=LLM_MODEL_API_KEY,
        base_url=LLM_MODEL_BASE_URL,
        cache_response=True,  # Enable response caching
        cache_ttl=7200,  # Optional: cache expires after 1 hour
        cache_dir=".agno/cache/model_responses"  # Optional: custom location
    ),
    tools=[
        memory_tools, 
        ReasoningTools(add_instructions=True, add_few_shot=True, enable_think=True, enable_analyze=True),
        CalculatorTools(), 
        policy_tools
    ],
    description="Enterprise policy analysis agent with access to company policy documents.",
    instructions=dedent("""
    You are an enterprise policy analysis agent with access to company policy documents.

    CRITICAL RULES:
    1. Use ONLY the retrieved policy content from the knowledge base
    2. Preserve EXACT tables and formatting from source documents
    3. If a table exists in the source (like approval hierarchies), reproduce it exactly
    4. Always include proper spacing between words and sections
    5. Use proper markdown formatting

    RESPONSE FORMAT:
    
    ## [Policy Name]
    
    Brief description based on the retrieved content.
    
    ### Key Details
    
    [Present tables EXACTLY as they appear in source documents]
    
    | Column 1 | Column 2 |
    |----------|----------|
    | Value 1  | Value 2  |
    
    - Important points from the policy
    - Another key point
    
    **Note:** Always base your response on the actual retrieved content.

    Available Tools:
    - step_counter: Count keyword occurrences
    - calculator: Perform calculations
    - role_lookup: Get role-based permissions
    - memory_tools: Store user preferences

    Focus on accuracy and presenting the ACTUAL policy content from the knowledge base.
    """),
    db=db,
    # user_id and session_id are None here - will be provided dynamically by AgentOS per request
    memory_manager=memory_manager,
    enable_user_memories=True,  # Automatically extracts memories from conversations
    add_history_to_context=True,
    num_history_runs=10,
    knowledge=knowledge,
    update_knowledge=True,
    add_knowledge_to_context=True,
    search_knowledge=True,
    markdown=True,
    debug_mode=True,
    # session_summary_manager=session_summary_manager,
    # enable_session_summaries=True,
    # reasoning=True,
    # reasoning_model=OpenAIChat(
    #     id="gpt-5",
    #     api_key=LLM_MODEL_API_KEY,
    #     base_url=LLM_MODEL_BASE_URL,
    # ),
    # reasoning_agent=,
    # reasoning_min_steps=1,
    # reasoning_max_steps=10,
)

# Test the agent when run directly
if __name__ == "__main__":
    openai_rag_agent.print_response(
        "Tell me about Sales Approval Policy",
        stream=True,
    )