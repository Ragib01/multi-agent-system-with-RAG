"""
FastAPI Multi-Agent System with RAG
Multi-Agent Architecture: Coordinator + Information Retrieval Agent + Analysis Agent
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
from app.agents.coordinator_agent import run_multi_agent_query, coordinator_team

app = FastAPI(
    title="Multi-Agent Policy Assistant",
    description="AI-powered assistant for company policies with RAG and agentic reasoning",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


class QueryRequest(BaseModel):
    query: str
    session_id: str


class AgentResponse(BaseModel):
    answer: str
    sources: List[str]
    tools_used: List[str]
    reasoning_steps: List[str]


@app.get("/")
async def root():
    return {
        "message": "Multi-Agent Policy Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "query": "/agentic/query (POST)",
            "streaming": "/agentic/query/streaming (POST)"
        }
    }


@app.post("/agentic/query", response_model=AgentResponse)
async def query_agent(request: QueryRequest):
    """
    Process employee queries about company policies using multi-agent RAG system.
    
    Multi-Agent Workflow:
    1. Coordinator Agent receives the query
    2. Information Retrieval Agent (IRA) retrieves relevant policy documents
    3. Analysis Agent (AA) analyzes content and uses tools (counter, calculator, role_lookup)
    4. Coordinator aggregates results and returns structured response
    """
    try:
        # Run the multi-agent query workflow
        result = run_multi_agent_query(
            query=request.query,
            session_id=request.session_id
        )
        
        return AgentResponse(
            answer=result["answer"],
            sources=result["sources"],
            tools_used=result["tools_used"],
            reasoning_steps=result["reasoning_steps"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.post("/agentic/query/streaming")
async def query_agent_streaming(request: QueryRequest):
    """
    Stream responses from the multi-agent system in real-time.
    
    Returns Server-Sent Events (SSE) stream with:
    - Thinking/reasoning steps as they happen
    - Sources being retrieved
    - Final answer chunks
    """
    async def event_generator():
        try:
            # Send initial thinking event
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Analyzing your query...'})}\n\n"
            
            # Send reasoning steps
            yield f"data: {json.dumps({'type': 'reasoning', 'step': 'Delegating to Information Retrieval Agent'})}\n\n"
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Searching knowledge base...'})}\n\n"
            
            yield f"data: {json.dumps({'type': 'reasoning', 'step': 'Retrieving relevant policy documents'})}\n\n"
            
            # Send sources being used
            yield f"data: {json.dumps({'type': 'source', 'source': 'Organization Policies & Processes Manual'})}\n\n"
            
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Analyzing retrieved content...'})}\n\n"
            yield f"data: {json.dumps({'type': 'reasoning', 'step': 'Analysis Agent processing content'})}\n\n"
            
            # Run the team with streaming
            response_text = ""
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Generating response...'})}\n\n"
            
            skip_mode = False
            for chunk in coordinator_team.run(
                input=request.query,
                session_id=request.session_id,
                stream=True,
            ):
                if hasattr(chunk, 'content') and chunk.content:
                    content = chunk.content
                    content_lower = content.lower()
                    
                    # Detect JSON blocks and tool outputs to skip
                    if ('search_knowledge_base' in content_lower or 
                        'completed in' in content_lower or
                        'retrieved_content' in content_lower or
                        '```json' in content_lower or
                        (skip_mode and ('{' in content or '}' in content or '"retrieved_content"' in content))):
                        skip_mode = True
                        continue
                    
                    # Stop skipping when we see markdown header (actual content starts)
                    if skip_mode and content.strip().startswith('#'):
                        skip_mode = False
                    
                    # Skip content while in skip mode
                    if skip_mode:
                        continue
                    
                    # Yield actual content
                    response_text += content
                    yield f"data: {json.dumps({'type': 'content', 'chunk': content})}\n\n"
            
            # Get full result with metadata
            result = run_multi_agent_query(
                query=request.query,
                session_id=request.session_id
            )
            
            # Send final metadata
            yield f"data: {json.dumps({'type': 'metadata', 'reasoning_steps': result['reasoning_steps'], 'sources': result['sources'], 'tools_used': result['tools_used']})}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'done', 'full_response': response_text})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

