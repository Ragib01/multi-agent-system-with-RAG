"""
FastAPI RAG Agent System
Uses rag_agent.py as the main agent for policy queries with single vector search
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
from app.agents.rag_agent import openai_rag_agent

app = FastAPI(
    title="Policy Assistant API",
    description="AI-powered assistant for company policies using RAG",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        "message": "Policy Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "query": "/agentic/query (POST)",
            "streaming": "/agentic/query/streaming (POST)"
        }
    }


@app.post("/agentic/query", response_model=AgentResponse)
async def query_agent(request: QueryRequest):
    """
    Process employee queries about company policies using RAG agent.
    """
    try:
        # Run RAG agent
        response = openai_rag_agent.run(
            input=request.query,
            session_id=request.session_id,
            stream=False,
        )
        
        answer = response.content if hasattr(response, 'content') else str(response)
        
        # Default metadata
        sources = ["Organization Policies & Processes Manual"]
        tools_used = ['knowledge_search', 'reasoning']
        reasoning_steps = [
            "Searched knowledge base for relevant policies",
            "Analyzed retrieved content",
            "Generated comprehensive response"
        ]
        
        return AgentResponse(
            answer=answer,
            sources=sources,
            tools_used=tools_used,
            reasoning_steps=reasoning_steps
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.post("/agentic/query/streaming")
async def query_agent_streaming(request: QueryRequest):
    """
    Stream responses from the RAG agent in real-time.
    Uses single vector search from rag_agent.py knowledge base.
    """
    async def event_generator():
        try:
            # Step 1: RAG Agent receives query
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'RAG Agent analyzing query...'})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'RAG Agent', 'step': 'Received query and searching knowledge base', 'status': 'in_progress'})}\n\n"
            
            # Step 2: Search knowledge base (SINGLE search using rag_agent's knowledge)
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Searching policy documents...'})}\n\n"
            
            search_results = openai_rag_agent.knowledge.search(request.query)
            total_chunks = len(search_results)
            found_docs = total_chunks > 0
            
            sources = []
            if found_docs:
                for doc in search_results:
                    meta = getattr(doc, 'metadata', {}) or {}
                    source_name = meta.get('source') or meta.get('name') or meta.get('filename') or 'Organization Policy'
                    sources.append(source_name)
                
                unique_sources = list(set(sources))
                for source in unique_sources:
                    yield f"data: {json.dumps({'type': 'source', 'source': source})}\n\n"
                
                ira_msg = f"Found {total_chunks} policy sections"
                yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'RAG Agent', 'step': 'Retrieved relevant policy sections', 'status': 'completed', 'response': ira_msg})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'RAG Agent', 'step': 'No relevant policy documents found', 'status': 'completed', 'response': 'Proceeding with general knowledge'})}\n\n"
            
            # Step 3: Generate response with streaming
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Generating response...'})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'RAG Agent', 'step': 'Analyzing content and generating response', 'status': 'in_progress'})}\n\n"
            
            response_text = ""
            
            # Stream from RAG agent
            for chunk in openai_rag_agent.run(
                input=request.query,
                session_id=request.session_id,
                stream=True,
            ):
                if hasattr(chunk, 'content') and chunk.content:
                    content = chunk.content
                    response_text += content
                    yield f"data: {json.dumps({'type': 'content', 'chunk': content})}\n\n"
            
            # Step 4: RAG Agent completed
            yield f"data: {json.dumps({'type': 'agent_step', 'agent': 'RAG Agent', 'step': 'Response generation complete', 'status': 'completed', 'response': 'Successfully generated policy response'})}\n\n"
            
            # Send final metadata
            reasoning_steps = [
                "Searched knowledge base for relevant policies",
                "Retrieved and analyzed policy documents",
                "Generated comprehensive response"
            ]
            tools_used = ['knowledge_search', 'reasoning']
            final_sources = unique_sources if found_docs else ["Organization Policies & Processes Manual"]
            
            yield f"data: {json.dumps({'type': 'metadata', 'reasoning_steps': reasoning_steps, 'sources': final_sources, 'tools_used': tools_used})}\n\n"
            
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
