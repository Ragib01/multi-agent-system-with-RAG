"""
Information Retrieval Agent (IRA)
Retrieves relevant text chunks from policy documents
"""
import os
from dotenv import load_dotenv
from textwrap import dedent

from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector, SearchType
from agno.knowledge.embedder.openai import OpenAIEmbedder

load_dotenv()

# Get environment variables
POSTGRES_DB_URL = os.getenv("POSTGRES_DB_URL")
LLM_MODEL_API_KEY = os.getenv("LLM_MODEL_API_KEY")
LLM_MODEL_BASE_URL = os.getenv("LLM_MODEL_BASE_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

os.environ["OPENAI_API_KEY"] = LLM_MODEL_API_KEY

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
        search_type=SearchType.hybrid,
        embedder=embedder,
    ),
    max_results=3,
)

information_retrieval_agent = Agent(
    name="Information Retrieval Agent",
    model=OpenAIChat(
        id="gpt-4o-mini",
        api_key=LLM_MODEL_API_KEY,
        base_url=LLM_MODEL_BASE_URL,
    ),
    description="Retrieves relevant policy document chunks based on queries.",
    instructions=dedent("""
    You are an Information Retrieval Agent specialized in finding relevant policy information.
    
    IMPORTANT: Do NOT use conversational fillers or introductory remarks. 
    Focus ONLY on retrieving and returning the requested information in JSON format.
    
    Your task:
    1. Search the knowledge base for relevant policy sections
    2. Return the most relevant content chunks
    3. Provide source information
    
    Return your findings in JSON format:
    {
        "retrieved_content": [
            {
                "content": "text content",
                "source": "document name",
                "relevance": "why this is relevant"
            }
        ],
        "total_chunks": number
    }
    """),
    knowledge=knowledge,
    search_knowledge=True,
    add_knowledge_to_context=True,
    markdown=True,
)

