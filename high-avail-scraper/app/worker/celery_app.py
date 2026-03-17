from celery import Celery

app = Celery(
    "high_avail_scraper",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=["app.worker.tasks"],
)
