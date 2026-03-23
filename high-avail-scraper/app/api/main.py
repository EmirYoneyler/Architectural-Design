from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.worker.tasks import scrape_target_site
from app.core.database import SessionLocal, ScrapeLog

app = FastAPI(title="High Availability Scraper Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
@app.get("/logs")
def get_all_logs():
    db = SessionLocal()
    logs = db.query(ScrapeLog).all()
    db.close()
    return logs