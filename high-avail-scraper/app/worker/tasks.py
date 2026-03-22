from wsgiref import headers

import httpx
import os
from celery import Celery
from app.core.identity import identity_manager

app = Celery(
    "scraper",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

@app.task(bind=True,max_retries=5)
def scrape_target_site(self,url):
    identity = identity_manager.get_identity()
    headers = {"User-Agent": identity["user_agent"]}
    proxy=identity["proxy"]
    proxy = None
    
    try:
        
        with httpx.Client(proxy=None, headers=headers, timeout=10.0, follow_redirects=True) as client:
            response = client.get(url)
            if response.status_code in [403, 429]:
                raise httpx.HTTPStatusError(f"we got blocked with status code {response.status_code}", request=response.request, response=response)
            
            
            return {
                "url": url,
                "status_code": response.status_code,
                "data_length": len(response.content),
                "used_proxy": proxy,
            }
        #         # Process the response as needed
    except Exception as exc:
        wait_time = 2 ** self.request.retries
        print(f"Error scraping {url}: {exc}. Retrying in {wait_time} seconds...")
        raise self.retry(exc=exc, countdown=wait_time)