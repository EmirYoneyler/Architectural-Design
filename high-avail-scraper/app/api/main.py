from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import HttpUrl
from fastapi import FastAPI
from app.worker.tasks import scrape_target_site

app = FastAPI(title="High Availability Scraper Orchestrator")

task_db = {}

@app.post("/scrape")
async def create_scrape_task(url: str):
    async_result = scrape_target_site.delay(url)
    task_id = async_result.id
    task_db[task_id] = {"url": url, "status": "pending"}
    return {"task_id": task_id, "url": url, "status": "pending"}


@app.get("/scrape/{job_id}")
async def get_scrape_task(job_id: str):
    from celery.result import AsyncResult

    res = AsyncResult(job_id)
    return {
        "job_id": job_id,
        "state": res.state,
        "result": res.result if res.state == "SUCCESS" else None
    }