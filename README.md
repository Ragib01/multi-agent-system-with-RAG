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
## Streaming API

### POST `/agentic/query/streaming`

Stream responses from the RAG agent in real-time using Server-Sent Events (SSE). This endpoint provides a Claude-like streaming experience with live updates of agent reasoning steps, sources, and markdown-formatted content.

#### Request

```json
{
  "query": "Tell me about Sales & Marketing Policies",
  "session_id": "employee_001"
}
```

#### Response Format

The API streams events in Server-Sent Events (SSE) format with the following event types:

**1. Thinking Events**
```json
{"type": "thinking", "message": "RAG Agent analyzing query..."}
```

**2. Agent Step Events**
```json
{
  "type": "agent_step",
  "agent": "RAG Agent",
  "step": "Searching knowledge base for relevant policy documents",
  "status": "in_progress" | "completed",
  "response": "Found 3 policy sections"
}
```

**3. Source Events**
```json
{"type": "source", "source": "Organization Policies & Processes Manual"}
```

**4. Content Events** (Streamed in chunks)
```json
{"type": "content", "chunk": "## Sales Approval Policy\n\n..."}
```

**5. Metadata Event** (Final metadata)
```json
{
  "type": "metadata",
  "reasoning_steps": ["step 1", "step 2", ...],
  "sources": ["source1", "source2"],
  "tools_used": ["knowledge_search", "reasoning"]
}
```

**6. Done Event**
```json
{"type": "done", "full_response": "Complete markdown response..."}
```

**7. Error Event**
```json
{"type": "error", "message": "Error description"}
```

#### Usage Example

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/agentic/query/streaming",
    json={
        "query": "Tell me about Sales Approval Policy",
        "session_id": "employee_001"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data = json.loads(line_str[6:])
            if data['type'] == 'content':
                print(data['chunk'], end='', flush=True)
```

**JavaScript/TypeScript:**
```javascript
const eventSource = new EventSource('http://localhost:8000/agentic/query/streaming', {
  method: 'POST',
  body: JSON.stringify({
    query: "Tell me about Sales Approval Policy",
    session_id: "employee_001"
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'content') {
    // Append chunk to UI
    document.getElementById('response').innerHTML += data.chunk;
  } else if (data.type === 'thinking') {
    // Show thinking indicator
    console.log('Thinking:', data.message);
  }
};
```

**cURL:**
```bash
curl -X POST "http://localhost:8000/agentic/query/streaming" \
  -H "Content-Type: application/json" \
  -N \
  -d '{
    "query": "Tell me about Sales Approval Policy",
    "session_id": "employee_001"
  }'
```

#### Features

- **Real-time Updates**: See agent reasoning steps and sources as they're discovered
- **Live Markdown Streaming**: Content streams in chunks as it's generated
- **Agent Transparency**: Track the RAG Agent's workflow steps in real-time
- **Source Attribution**: See which policy documents are being used
- **Error Handling**: Graceful error events for debugging
- **Session Support**: Maintains conversation context via `session_id`

#### Architecture

The streaming endpoint:
1. Performs a **single vector search** using the RAG agent's knowledge base
2. Streams agent steps and source discovery
3. Streams markdown-formatted content chunks in real-time
4. Provides final metadata (reasoning steps, sources, tools used) at completion

This ensures efficient, single-pass knowledge retrieval while providing a rich streaming experience.

---

## Example Queries
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
   - Improve the markdown response

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


