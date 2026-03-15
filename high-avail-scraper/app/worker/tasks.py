from celery import Celery
import time
import random
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6373/0")
app = Celery('tasks', broker=redis_url, backend=redis_url)

@app.task(bind=True, max_retries=3, queue="scraper")
def scrape_target_site(self,url):
    try:
        print(f"[*]{url} - Scraping started.")
        if random.random() < 0.3:  # Simulate a failure with 30% chance
            raise Exception("Simulated scraping failure.")
        time.sleep(2)
        return {"url": url, "status": "success", "data": f"Scraped data from {url}"}  # Simulate variable scraping time
    except Exception as exc:
        print(f"[*]{url} - Scraping failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    