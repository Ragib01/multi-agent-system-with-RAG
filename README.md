# Multi-Agent Policy Assistant with RAG

A FastAPI-based multi-agent system that answers employee questions about company policies using RAG (Retrieval-Augmented Generation), agentic reasoning, and tool orchestration.

## Features

- **Multi-Agent Architecture**: Integrated agent with knowledge retrieval, reasoning, and tool usage
- **RAG System**: Vector-based knowledge retrieval from policy documents using PgVector
- **Session Memory**: Maintains conversation context for follow-up queries
- **Tool Orchestration**: Built-in tools for counting, calculations, and role lookups
- **Structured Output**: Pydantic-validated responses with reasoning steps
- **Memory Management**: Automatically extracts and stores user preferences

## Architecture

### Multi-Agent System

The system implements a **Coordinator + Worker Agents** pattern:

#### 1. **Coordinator Agent**
- Receives user queries
- Routes requests to appropriate worker agents
- Manages session memory and user context
- Aggregates results from worker agents
- Generates final structured response

#### 2. **Information Retrieval Agent (IRA)**
- Retrieves relevant policy document chunks from vector database
- Uses hybrid search (semantic + keyword)
- Returns top 3 most relevant content chunks
- Provides source attribution

#### 3. **Analysis Agent (AA)**
- Receives retrieved content from IRA
- Analyzes policy information using LLM reasoning
- Uses specialized tools as needed:
  - `step_counter`: Count keyword occurrences (e.g., "approval" steps)
  - `calculator`: Perform arithmetic calculations
  - `role_lookup`: Get role-based permissions and approval limits
- Generates detailed insights and findings

### Workflow

```
User Query → Coordinator Agent
              ↓
         IRA (Retrieve Policy Content)
              ↓
         AA (Analyze + Use Tools)
              ↓
         Coordinator (Aggregate Results)
              ↓
         Structured Response
```

### Context Engineering

- **Session Management**: Each query maintains session context via `session_id`
- **Memory Extraction**: Automatically stores user preferences and information
- **Conversation History**: Keeps last 2 conversation runs for context
- **Knowledge Context**: Injects relevant policy sections into prompts

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL with pgvector extension
- OpenAI-compatible LLM API (e.g., LM Studio, OpenAI)

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:

```env
POSTGRES_DB_URL=postgresql://user:password@localhost:5432/dbname
LLM_MODEL_API_KEY=your-api-key
LLM_MODEL_BASE_URL=https://api.openai.com/v1
RAG_AGENT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small 
```

4. Initialize the knowledge base:

```bash
python vectorizer/vectorizer.py
```

## Running the API

### Start the server:

```bash
python run_api.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoint

### POST `/agentic/query`

Process employee queries about company policies.

**Request:**
```json
{
  "query": "Summarize the steps for requesting hardware approval.",
  "session_id": "employee_001"
}
```

**Response:**
```json
{
  "answer": "Detailed answer with markdown formatting...",
  "sources": ["Organization Policies & Processes Manual"],
  "tools_used": ["knowledge_search", "step_counter"],
  "reasoning_steps": [
    "Received and analyzed query",
    "Searched knowledge base for hardware approval policy",
    "Used step_counter to count approval steps",
    "Generated comprehensive response"
  ]
}
```

Example queries:
- "Summarize the steps for requesting hardware approval."
- "How many steps in the onboarding process require HR approval?"
- "What are the approval limits for a manager role?"

## Design Patterns

### 1. Multi-Agent Coordination
The Coordinator Agent orchestrates the workflow:
- Receives and understands user queries
- Delegates to Information Retrieval Agent for document search
- Passes retrieved content to Analysis Agent
- Aggregates results from all agents
- Maintains conversation context across queries

### 2. Agentic Reasoning
Each agent has specialized reasoning:
- **IRA**: Semantic understanding to find relevant policy sections
- **AA**: Deep analysis, tool selection, and insight generation
- **Coordinator**: Result aggregation and response synthesis

### 3. Tool Orchestration
Tools are available to the Analysis Agent:
- Automatically decides when tools are needed
- Executes tool calls based on query requirements
- Multiple tools can be chained in a single analysis
- Tool results are incorporated into final response

### 4. Context Engineering
Context is managed at multiple levels:
- **Session Memory**: Coordinator maintains conversation history (10 runs)
- **User Preferences**: Automatically extracted and stored
- **Knowledge Context**: IRA provides relevant document chunks
- **Agent Communication**: Results passed between agents

### 5. Structured Output
All responses follow a consistent schema:
- Clear answer in markdown format
- Source attribution from IRA
- Tool usage transparency from AA
- Step-by-step reasoning from all agents

## Trade-offs and Improvements

### Current Design
- **Pros**: 
  - Clear separation of concerns (Coordinator, IRA, AA)
  - Specialized agents for retrieval and analysis
  - Scalable architecture for adding more agents
  - Better debugging and monitoring per agent
- **Cons**: 
  - More complex than single agent
  - Sequential processing (could be parallelized)
  - Multiple LLM calls increase latency

### Potential Improvements

1. **Parallel Agent Execution**:
   - Run IRA and AA in parallel where possible
   - Implement async agent communication
   - Reduce overall response time

2. **Enhanced Memory**:
   - Increase conversation history (currently 2 runs)
   - Add long-term memory summaries
   - Implement memory prioritization

3. **Advanced Tool Usage**:
   - Add document comparison tools
   - Implement workflow visualization
   - Add policy compliance checker

4. **Performance**:
   - Implement response caching
   - Add async processing for long queries
   - Optimize vector search parameters

5. **Monitoring**:
   - Add query analytics
   - Track tool usage statistics
   - Implement feedback collection

## Project Structure

```
ixora-chatbot/
├── app/
│   ├── agents/
│   │   ├── coordinator_agent.py           # Coordinator Agent
│   │   ├── information_retrieval_agent.py # IRA - Document retrieval
│   │   ├── analysis_agent.py              # AA - Content analysis
│   │   ├── rag_agent.py                   # Legacy single agent (backup)
│   │   └── __init__.py
│   ├── tools/
│   │   ├── policy_tools.py                # Policy analysis tools
│   │   └── __init__.py
│   └── main.py                            # FastAPI application
├── data/
│   ├── markdown/                          # Policy documents
│   └── pdf/                               # Source PDFs
├── vectorizer/
│   └── vectorizer.py                     # Knowledge base loader
├── run_api.py                            # API server script
├── README.md                             # Full documentation
├── QUICKSTART.md                         # Quick start guide
└── requirements.txt                      # Dependencies
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| POSTGRES_DB_URL | PostgreSQL connection URL | postgresql://user:pass@localhost:5432/db |
| LLM_MODEL_API_KEY | API key for LLM | sk-xxx or lm-studio |
| LLM_MODEL_BASE_URL | LLM API endpoint | https://api.openai.com/v1 or http://localhost:1234/v1|
| RAG_AGENT_MODEL | Model identifier | gpt-4o-mini |
| EMBEDDING_MODEL | Embedding model name | text-embedding-3-small or text-embedding-nomic-embed-text-v1.5 |


