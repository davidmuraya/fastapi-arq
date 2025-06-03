# FastAPI, ARQ + Redis

A production-ready FastAPI project for managing background task queues using [ARQ](https://github.com/samuelcolvin/arq) and Redis. This project demonstrates how to offload long-running or resource-intensive tasks from your FastAPI API to asynchronous workers, enabling scalable and reliable background job execution. It includes queue management endpoints, example producer/consumer patterns, and a modular structure for easy extension.

**Why ARQ and not Celery?**

This project uses ARQ instead of Celery because the task functions are asynchronous (`async def`). ARQ is designed for asyncio-based Python code and integrates seamlessly with async frameworks like FastAPI. In contrast, using Celery with async tasks requires additional setup and third-party libraries (such as `aio-celery`), making ARQ a simpler and more natural fit for async workloads.


## Features

- Asynchronous background task processing with ARQ
- FastAPI endpoints to enqueue and monitor tasks
- Integration with Redis for robust, production-grade queue management
- Example producer/consumer patterns (e.g., addition, division tasks, HTTP calls)
- Task status and result retrieval via API
- Modular codebase with clear separation of API, tasks, and configuration
- Optional in-memory queue support for development/testing
- Windows and Linux compatibility

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- ARQ
- Redis (for production queue backend)
- httpx (for async HTTP calls)
- pydantic

## Installation

```bash
git clone https://github.com/davidmuraya/fastapi-arq.git
cd fastapi-arq
pip install -r requirements.txt
```

Ensure you have Redis installed and running on your machine.

Create a `.env` file in the root directory and add the following lines:

```bash
REDIS_BROKER=localhost:6379
WORKER_QUEUE=app-LyiRY47QTMd
JOBS_DB=database/jobs.db
```

## Usage

### Running the project
To run the FastAPI application with ARQ worker, follow these steps:

```bash
uvicorn main:app --reload --port 5000
```

### Running the ARQ Worker
To start the ARQ worker that processes background tasks, run the following command in a separate terminal:
```bash
arq worker:WorkerSettings
```

### Example: Enqueue an Addition Task

```bash
curl -X POST "http://localhost:5000/tasks/add" -H "Content-Type: application/json" -d "{\"x\": 5, \"y\": 10}"
```

### Example: Check Job Status

```bash
curl "http://localhost:5000/jobs/<job_id>"
```

## Project Structure

```
fastapi-arq/
├── .env                    # Environment variables (not committed)
├── .gitignore              # Specifies intentionally untracked files that Git should ignore
├── config.py               # Environment configuration loading
├── database/
│   ├── connection.py       # Database connection setup (engine, session provider)
│   ├── __init__.py
│   └── models.py           # SQLModel database table definitions (e.g., JobHistory)
├── main.py                 # FastAPI application, API endpoints
├── models.py               # Pydantic models for API requests and responses (e.g., JobStatusResponse)
├── README.md               # This file: Project documentation
├── redis_pool.py           # ARQ Redis connection pool dependency
├── requirements.txt        # Python package dependencies
├── schemas/
│   ├── __init__.py
│   └── models.py           # Pydantic schemas for data validation (e.g., JobHistoryCreate, JobHistoryRead)
├── tasks.py                # ARQ task definitions (e.g., add, divide)
├── utils/
│   ├── date_parser.py      # Utility for parsing datetime strings
│   ├── events.py           # FastAPI startup/shutdown event handlers
│   ├── __init__.py
│   ├── job_info.py         # Utility for processing ARQ job information
│   └── job_info_crud.py    # CRUD operations for the JobHistory database table
└── worker.py               # ARQ worker settings and configuration
```

## Configuration

- Configure queue backend and worker settings in `worker.py` and via environment variables (`.env` file).

## License

MIT License

---
