from app.core.database import SessionLocal, ScrapeLog

import httpx
import os
from celery import Celery
from app.core.identity import identity_manager

app = Celery(
    "scraper",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)


def _http_verify_setting():
    ca_bundle = os.getenv("SCRAPER_CA_BUNDLE")
    if ca_bundle:
        return ca_bundle

    verify_ssl = os.getenv("SCRAPER_SSL_VERIFY", "true").strip().lower()
    return verify_ssl not in {"0", "false", "no", "off"}

@app.task(bind=True,max_retries=5)
def scrape_target_site(self,url):
    identity = identity_manager.get_identity()
    headers = {"User-Agent": identity["user_agent"]}
    proxy=identity["proxy"]
    proxy = None
    
    try:
        
        with httpx.Client(
            proxy=None,
            headers=headers,
            timeout=10.0,
            follow_redirects=True,
            verify=_http_verify_setting(),
        ) as client:
            response = client.get(url)
            #kayıt kısmı
            db = SessionLocal()
            new_log = ScrapeLog(
                url=url,
                status_code=response.status_code,
                html_size=len(response.text)
            )
            db.add(new_log)
            db.commit()
            db.close()
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