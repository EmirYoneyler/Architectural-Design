# Architectural-Design

## High Availability Web Scraper Orchestrator

This project implements a **fault-tolerant, asynchronous web scraping system** built with FastAPI, Celery, and Redis. It is designed to scrape URLs at scale while automatically rotating identities (user agents and proxies) to avoid detection and handling failures through configurable exponential-backoff retries.

---

## Architecture

```
┌─────────────┐    POST /scrape     ┌───────────────────┐
│   Client    │ ──────────────────► │  FastAPI Server   │
│             │ ◄────────────────── │  (api/main.py)    │
│             │    {task_id}        └────────┬──────────┘
│             │                              │ .delay(url)
│             │    GET /scrape/{id}          ▼
│             │ ──────────────────► ┌───────────────────┐     ┌──────────┐
│             │ ◄────────────────── │  Celery Worker    │ ◄── │  Redis   │
│             │    {state, result}  │  (worker/tasks)   │ ──► │  Broker  │
└─────────────┘                     └────────┬──────────┘     └──────────┘
                                             │
                                    ┌────────▼──────────┐
                                    │  IdentityManager  │
                                    │  (core/identity)  │
                                    │  • User-Agent     │
                                    │  • Proxy rotation │
                                    └───────────────────┘
```

### Components

| Module | File | Responsibility |
|---|---|---|
| **API Server** | `app/api/main.py` | FastAPI REST endpoints; dispatches Celery tasks and polls results |
| **Celery App** | `app/worker/celery_app.py` | Celery application configured with Redis broker/backend |
| **Scrape Task** | `app/worker/tasks.py` | Core scraping logic with retry/backoff and blocking detection |
| **Identity Manager** | `app/core/identity.py` | Randomly rotates user agents and proxy servers per request |

---

## How It Works

1. A client sends `POST /scrape?url=<target>`.
2. The API server enqueues a Celery task and immediately returns a `task_id`.
3. A Celery worker picks up the task, selects a random user agent and proxy via `IdentityManager`, then makes the HTTP request using `httpx`.
4. If the server responds with **403** or **429** (blocked/rate-limited), or any other error occurs, the task is retried up to **5 times** with exponential backoff (`2^attempt` seconds).
5. On success the result (URL, status code, response size, proxy used) is stored in Redis.
6. The client polls `GET /scrape/{task_id}` to retrieve the final state and result.

---

## REST API

### `POST /scrape`

Enqueue a new scraping job.

**Query parameter**: `url` — the target URL to scrape.

```
POST /scrape?url=https://example.com
```

**Response**:
```json
{
  "task_id": "abc123",
  "url": "https://example.com",
  "status": "pending"
}
```

### `GET /scrape/{job_id}`

Poll the status of a scraping job.

```
GET /scrape/abc123
```

**Response**:
```json
{
  "job_id": "abc123",
  "state": "SUCCESS",
  "result": {
    "url": "https://example.com",
    "status_code": 200,
    "data_length": 12483,
    "used_proxy": null
  }
}
```

Possible `state` values: `PENDING`, `STARTED`, `SUCCESS`, `FAILURE`, `RETRY`.

---

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Run with Docker Compose

```bash
cd high-avail-scraper
docker compose up --build
```

This starts three services:
- **redis** — message broker and result backend
- **api** — FastAPI server on `http://localhost:8000`
- **worker** — Celery worker processing scrape tasks

### Run Locally (without Docker)

```bash
cd high-avail-scraper
pip install -r requirements.txt

# Terminal 1 – start Redis (requires a local Redis instance)
redis-server

# Terminal 2 – start the Celery worker
celery -A app.worker.celery_app worker --loglevel=info

# Terminal 3 – start the FastAPI server
uvicorn app.api.main:app --reload
```

---

## Project Structure

```
high-avail-scraper/
├── app/
│   ├── api/
│   │   └── main.py            # FastAPI application & REST endpoints
│   ├── core/
│   │   └── identity.py        # IdentityManager: user-agent & proxy rotation
│   └── worker/
│       ├── celery_app.py      # Celery application instance
│       └── tasks.py           # scrape_target_site Celery task
├── docker-compose.yml
└── requirements.txt
```
