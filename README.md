# FastAPI, ARQ + Redis

A production-ready FastAPI project for managing background task queues using [ARQ](https://github.com/samuelcolvin/arq) and Redis. This project demonstrates how to offload long-running or resource-intensive tasks from your FastAPI API to asynchronous workers, enabling scalable and reliable background job execution. It includes queue management endpoints, example producer/consumer patterns, and a modular structure for easy extension.

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
WORKER_QUEUE=app-LyiRY47QTM
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
├── config.py               # Environment configuration
├── main.py                 # FastAPI app and endpoints
├── models.py               # Pydantic models for requests and responses
├── redis_pool.py           # Redis connection pool dependency
├── requirements.txt        # Python dependencies
├── tasks.py                # ARQ task definitions
├── worker.py               # ARQ worker configuration
├── .env                    # Environment variables (not committed)
└── README.md               # Project documentation
```

## Configuration

- Configure queue backend and worker settings in `worker.py` and via environment variables (`.env` file).

## License

MIT License

---
