"""
Browser Use API - AI-Powered Web Scraping
FastAPI service using browser-use for reliable, AI-guided web scraping.
"""
import os
import asyncio
import json
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Request models
class ScrapeRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    task: str = Field(
        default="Extract all visible content from this page",
        description="What to extract or do on the page"
    )
    model: str = Field(default="gpt-4o-mini", description="Model to use")

class BatchScrapeRequest(BaseModel):
    urls: List[str] = Field(..., description="List of URLs to scrape")
    task: str = Field(default="Extract all visible content from each page")

# In-memory storage for async jobs
jobs = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    print("🚀 Browser Use API starting...")
    yield
    print("👋 Browser Use API shutting down...")

app = FastAPI(
    title="Browser Use API",
    description="AI-Powered Web Scraping - Uses browser-use to reliably scrape any website",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "Browser Use API",
        "version": "1.0.0",
        "description": "AI-Powered Web Scraping using browser-use",
        "docs": "/docs",
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    """Scrape a URL using browser-use AI agent."""
    job_id = f"scrape_{datetime.now().timestamp()}"
    jobs[job_id] = {"status": "starting", "url": request.url}
    
    try:
        from browser_use_sdk.v3 import AsyncBrowserUse
        
        client = AsyncBrowserUse()
        jobs[job_id]["status"] = "running"
        
        result = await client.run(
            task=f"{request.task}. URL: {request.url}",
            model=request.model,
        )
        
        jobs[job_id]["status"] = "completed"
        
        return {
            "job_id": job_id,
            "success": True,
            "url": request.url,
            "content": result.output if hasattr(result, 'output') else str(result),
            "model": request.model,
        }
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape/batch")
async def scrape_batch(request: BatchScrapeRequest, background_tasks: BackgroundTasks):
    """Submit batch scraping job."""
    job_id = f"batch_{datetime.now().timestamp()}"
    jobs[job_id] = {
        "status": "pending",
        "total": len(request.urls),
        "completed": 0,
        "results": []
    }
    
    background_tasks.add_task(run_batch_job, job_id, request)
    
    return {
        "job_id": job_id,
        "status_url": f"/jobs/{job_id}",
    }

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a scraping job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    """Get results of a completed job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not ready: {job['status']}")
    
    return job["results"]

async def run_batch_job(job_id: str, request: BatchScrapeRequest):
    """Background batch scraping."""
    from browser_use_sdk.v3 import AsyncBrowserUse
    
    client = AsyncBrowserUse()
    jobs[job_id]["status"] = "running"
    
    results = []
    for i, url in enumerate(request.urls):
        try:
            result = await client.run(
                task=f"{request.task}. URL: {url}",
            )
            results.append({
                "url": url,
                "success": True,
                "content": result.output if hasattr(result, 'output') else str(result),
            })
        except Exception as e:
            results.append({
                "url": url,
                "success": False,
                "error": str(e),
            })
        
        jobs[job_id]["completed"] = i + 1
    
    jobs[job_id]["status"] = "completed"
    jobs[job_id]["results"] = results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))