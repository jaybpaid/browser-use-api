"""
Browser Use API - AI-Powered Web Scraping
Uses Playwright for reliable browser automation.
"""
import os
import asyncio
import json
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Browser Use API",
    description="AI-Powered Web Scraping with browser automation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ScrapeRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    task: str = Field(
        default="Extract all visible content from the page",
        description="What to extract or do"
    )
    wait_for: Optional[str] = Field(
        default=None,
        description="CSS selector to wait for before returning"
    )

class BatchRequest(BaseModel):
    urls: List[str] = Field(..., description="List of URLs to scrape")
    task: str = Field(default="Extract all content from each page")

# Job storage
jobs = {}

from playwright.async_api import async_playwright as pw

async def scrape_with_playwright(url: str, task: str = "Extract all content") -> dict:
    """Scrape a URL using Playwright."""
    browser = None
    try:
        async with pw() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                ]
            )
            
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            page = await context.new_page()
            
            # Navigate and wait
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1000)  # Wait for JS
            
            # Get content
            content = await page.content()
            title = await page.title()
            
            # Try to extract specific data
            try:
                # Get main text content
                text = await page.inner_text("body")
            except:
                text = content
            
            await browser.close()
            
            return {
                "success": True,
                "url": url,
                "title": title,
                "content": text[:50000],  # Limit to 50k chars
                "html": content[:10000],  # First 10k of HTML
            }
            
    except Exception as e:
        if browser:
            await browser.close()
        return {
            "success": False,
            "url": url,
            "error": str(e)
        }

@app.get("/")
async def root():
    return {
        "service": "Browser Use API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    """Scrape a URL with Playwright."""
    result = await scrape_with_playwright(request.url, request.task)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Scraping failed"))
    
    return result

@app.post("/scrape/batch")
async def scrape_batch(request: BatchRequest, background_tasks: BackgroundTasks):
    """Batch scrape multiple URLs."""
    job_id = f"batch_{datetime.now().timestamp()}"
    jobs[job_id] = {
        "status": "pending",
        "total": len(request.urls),
        "completed": 0,
        "results": []
    }
    
    background_tasks.add_task(run_batch, job_id, request.urls, request.task)
    
    return {
        "job_id": job_id,
        "status_url": f"/jobs/{job_id}",
    }

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not ready: {job['status']}")
    
    return job["results"]

async def run_batch(job_id: str, urls: List[str], task: str):
    """Background batch scraping."""
    jobs[job_id]["status"] = "running"
    results = []
    
    for url in urls:
        result = await scrape_with_playwright(url, task)
        results.append(result)
        jobs[job_id]["completed"] += 1
    
    jobs[job_id]["status"] = "completed"
    jobs[job_id]["results"] = results

# Apify Actor entry point
async def main():
    """Run as Apify Actor."""
    from apify import Actor
    
    actor_input = await Actor.get_input()
    if not actor_input:
        raise ValueError("No input provided")
    
    url = actor_input.get("url")
    task = actor_input.get("task", "Extract all content")
    
    result = await scrape_with_playwright(url, task)
    
    await Actor.push_data(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))