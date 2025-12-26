import os
import asyncio
from pathlib import Path

from agno.knowledge.knowledge import Knowledge
from agno.knowledge.chunking.agentic import AgenticChunking
from agno.knowledge.embedder.openai import OpenAIEmbedder

from agno.vectordb.pgvector import PgVector, SearchType

from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.reader.markdown_reader import MarkdownReader

from dotenv import load_dotenv
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

from agno.models.lmstudio import LMStudio
from agno.agent.agent import Agent
async def main():
    embedder = OpenAIEmbedder(
        id=EMBEDDING_MODEL,
        api_key=LLM_MODEL_API_KEY,
        base_url=LLM_MODEL_BASE_URL,
        dimensions=768  # Add this for custom dimensions
    )

    knowledge = Knowledge(
        vector_db=PgVector(
            table_name="organization_policies_processes_vectors",
            db_url=POSTGRES_DB_URL,
            search_type=SearchType.hybrid, # SearchType.hybrid combines vector (semantic) and keyword (lexical) search for better results. 
            embedder=embedder,
        ),
        max_results=2,
    )

    # PDF Reader
    # await knowledge.add_content_async(
    #     name="orangebd_company_profile",
    #     url="https://www.orangebd.com/pdf/company_profile.pdf",
    #     metadata={"doc_type": "orangebd_company_profile_book"},
    #     reader=PDFReader(
    #         name="Agentic Chunking Reader",
    #         chunking_strategy=AgenticChunking(),
    #     ),
    # )
    
    
    # Markdown Reader
    # Get the project root directory (parent of vectorizer directory)
    project_root = Path(__file__).parent.parent
    markdown_path = project_root / "data" / "markdown" / "organization_policies_processes.md"
    
    await knowledge.add_content_async(
        name="Organization Policies & Processes Manual - IXORA",
        path=markdown_path,
        reader=MarkdownReader(
            name="Markdown Reader",
            chunking_strategy=AgenticChunking(),
        ),
    )
    

    agent = Agent(
        model=LMStudio(
            id=RAG_AGENT_MODEL,
            base_url=LLM_MODEL_BASE_URL,
            api_key=LLM_MODEL_API_KEY,
        ),
        # tools=[ReasoningTools(add_instructions=True, add_few_shot=True, enable_think=True, enable_analyze=True)],
        knowledge=knowledge,
        add_knowledge_to_context=True,
        search_knowledge=True,
        markdown=True,
    )

    await agent.aprint_response("Summarize the steps for requesting hardware approval.", stream=True, markdown=True)

if __name__ == "__main__":
    asyncio.run(main())
