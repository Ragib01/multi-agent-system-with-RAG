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
from app.agents import (
    information_retrieval_agent, 
    analysis_agent, 
    coordinator_team, 
    run_multi_agent_query
)

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
    - Agent-specific reasoning steps with their responses
    - Sources being retrieved
    - Final answer chunks
    """
    async def event_generator():
        try:
            # Step 1: Coordinator receives query
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Coordinator Agent analyzing query...'})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'Coordinator Agent', 'step': 'Received query and initiating multi-agent workflow', 'status': 'in_progress'})}\n\n"
            
            # Step 2: Information Retrieval Agent
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Information Retrieval Agent searching...'})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'Information Retrieval Agent', 'step': 'Searching knowledge base for relevant policy documents', 'status': 'in_progress'})}\n\n"
            
            # Run IRA to get dynamic results for the UI
            ira_response = information_retrieval_agent.run(input=request.query, stream=False)
            retrieved_content = ira_response.content if hasattr(ira_response, 'content') else str(ira_response)
            
            # Parse IRA response to see what was found
            found_docs = False
            total_chunks = 0
            sources = []
            try:
                # Handle potential JSON in the response
                json_str = retrieved_content
                if '```json' in json_str:
                    json_str = json_str.split('```json')[1].split('```')[0].strip()
                
                if json_str.strip().startswith('{'):
                    ira_data = json.loads(json_str)
                    total_chunks = ira_data.get('total_chunks', 0)
                    if total_chunks > 0:
                        found_docs = True
                        sources = [c.get('source', 'Organization Policy') for c in ira_data.get('retrieved_content', [])]
            except Exception:
                # Fallback if parsing fails but content seems to exist
                if len(retrieved_content) > 100:
                    found_docs = True
            
            if found_docs:
                unique_sources = list(set(sources))
                for source in unique_sources:
                    yield f"data: {json.dumps({'type': 'source', 'source': source})}\n\n"
                
                ira_msg = f"Found {total_chunks if total_chunks > 0 else 'relevant'} policy sections"
                yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'Information Retrieval Agent', 'step': 'Retrieved relevant policy sections', 'status': 'completed', 'response': ira_msg})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'Information Retrieval Agent', 'step': 'No relevant policy documents found', 'status': 'completed', 'response': 'Proceeding with general knowledge'})}\n\n"
            
            # Step 3: Analysis Agent
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Analysis Agent processing content...'})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'Analysis Agent', 'step': 'Analyzing retrieved content and applying tools', 'status': 'in_progress'})}\n\n"
            
            # Run the team with streaming
            response_text = ""
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Analysis Agent generating insights...'})}\n\n"
            
            skip_mode = False
            for chunk in coordinator_team.run(
                input=request.query,
                session_id=request.session_id,
                stream=True,
            ):
                if hasattr(chunk, 'content') and chunk.content:
                    content = chunk.content
                    content_lower = content.lower()
                    
                    # Detect JSON blocks, tool outputs, and conversational fillers to skip
                    if ('search_knowledge_base' in content_lower or 
                        'completed in' in content_lower or
                        'retrieved_content' in content_lower or
                        'reasoning_steps' in content_lower or
                        'tools_used' in content_lower or
                        'key_findings' in content_lower or
                        'ready to analyze' in content_lower or
                        'once it is retrieved' in content_lower or
                        'provide the necessary details' in content_lower or
                        'provide the document' in content_lower or
                        'waiting for' in content_lower or
                        'analyze the content' in content_lower or
                        'retrieving' in content_lower and 'policy' in content_lower or
                        '```json' in content_lower or
                        content.strip().startswith('{') or
                        (skip_mode and ('{' in content or '}' in content or '"' in content or ':' in content))):
                        skip_mode = True
                        continue
                    
                    # Stop skipping when we see actual markdown content starts
                    # We look for a markdown header or a significant piece of text that isn't JSON
                    if skip_mode:
                        stripped_content = content.strip()
                        if stripped_content.startswith('#') or (len(stripped_content) > 30 and not stripped_content.startswith('{') and not stripped_content.startswith('"')):
                             skip_mode = False
                    
                    # Skip content while in skip mode
                    if skip_mode:
                        continue
                    
                    # Yield actual content
                    response_text += content
                    yield f"data: {json.dumps({'type': 'content', 'chunk': content})}\n\n"
            
            # Step 4: Analysis Agent completed
            yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'Analysis Agent', 'step': 'Completed analysis and generated insights', 'status': 'completed', 'response': 'Analysis complete with tool usage and findings'})}\n\n"
            
            # Step 5: Coordinator aggregates
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Coordinator aggregating results...'})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'Coordinator Agent', 'step': 'Aggregating results from all agents', 'status': 'in_progress'})}\n\n"
            
            # Get full result with metadata
            result = run_multi_agent_query(
                query=request.query,
                session_id=request.session_id
            )
            
            yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'Coordinator Agent', 'step': 'Generated final comprehensive response', 'status': 'completed', 'response': 'Multi-agent workflow completed successfully'})}\n\n"
            
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

