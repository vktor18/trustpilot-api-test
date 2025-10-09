# Trustpilot PoC API

## Overview
This project is a **proof of concept** for building a small, clean API that ingests, validates, and serves Trustpilot review data.  
It’s not a production system — it’s an exercise in data ingestion, cleaning, and API design using **FastAPI**, **SQLAlchemy**, and **SQLite** for simplicity.  

The API reads mock review data from a CSV file, loads it into a database, normalizes it, and exposes endpoints to retrieve data in JSON or CSV form.  
It also demonstrates **streaming responses**, **idempotent ingestion**, and **clean testing isolation** — patterns that scale nicely to larger systems.

---

## Features
- **Data Ingestion** – Load and clean a CSV file (`tp_reviews.csv`) into an SQLite database.  
- **Data Cleaning** –  
  - Remove duplicate reviews.  
  - Validate and normalize review dates.  
  - Enforce valid rating ranges (1–5).  
- **API Endpoints** –  
  - `/business/{business_id}/reviews`: Get reviews for a specific business.  
  - `/user/{reviewer_id}/reviews`: Get reviews written by a user.  
  - `/user/{reviewer_id}/account`: Get user account info.  
- **Streaming Responses** – Efficiently stream CSVs for large result sets.  
- **Idempotent Inserts** – Use `INSERT ... ON CONFLICT` to prevent duplicates.  
- **Dockerized Setup** – Single command to build and run the stack.  
- **Makefile Commands** – Simplify build, run, and cleanup workflows.

---

## Requirements
- Python 3.11+  
- SQLite (default local DB)  
- Dependencies from `requirements.txt`  
- Docker (optional)

---

## Project Structure
```
trustpilot-api-test/
├── alembic/               # Database migrations
├── alembic.ini            # Alembic config
├── application.dockerfile # Dockerfile for API
├── entrypoint.sh          # Entrypoint script for Docker/local runs
├── load_data.py           # Data ingestion and cleaning script
├── main.py                # FastAPI application
├── models.py              # SQLAlchemy ORM models
├── requirements.txt       # Python dependencies
├── tp_reviews.csv         # Source data (CSV)
└── trustpilot_test.db     # SQLite database (created after ingestion)
```

## Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd trustpilot-api-test
```

### 2. If running locally, create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Using Docker
```bash
make run
```

### 4. Without Docker
```bash
chmod +x entrypoint.sh
LOAD_DATA=1 USE_ALEMBIC=1 ./entrypoint.sh
```

## Access the API
The API will be available at [http://localhost:8000](http://localhost:8000).

The API will trigger the download of the resulting CSV file when accessed via a web browser, except for the Get User Account Information which does not download the csv for simplicity.
## API Endpoints

### 1. Get Reviews for a Business
**GET** `/business/{business_id}/reviews`

**Example:**
```bash
curl -X GET "http://localhost:8000/business/123/reviews"
```

### 2. Get Reviews by a User
**GET** `/user/{reviewer_id}/reviews`

**Example:**
```bash
curl -X GET "http://localhost:8000/user/456/reviews"
```

### 3. Get User Account Information
**GET** `/user/{reviewer_id}/account`

**Example:**
```bash
curl -X GET "http://localhost:8000/user/456/account"
```

## Data Cleaning
The `load_data.py` script performs the following cleaning tasks:
- Removes duplicate reviews based on unique constraints.
- Validates and normalizes review dates to ensure consistency.
- Ensures ratings are within the valid range (1-5).


## ⚠️ Important Notes on Data Ingestion

The load_data.py script is intentionally a PoC utility — a lightweight bootstrapper for loading demo data into an empty database.
It is not a production-safe ingestion tool. There’s a fundamental distinction between schema migrations and data migrations in real systems, and this script blurs that line for simplicity.

Why this matters:

In production, rerunning data ingestion scripts is almost always the wrong move.
It can overwrite or duplicate data, corrupt referential integrity, or silently desynchronize content.

Schema migrations (e.g., Alembic upgrades) evolve the database structure.
They’re versioned, ordered, and safe to rerun.

Data ingestion, on the other hand, mutates live state. It should be deliberate, controlled, and ideally idempotent — typically handled by background jobs, message queues, or dedicated ingestion endpoints.

For this PoC, load_data.py exists to simulate the initial seeding of a dataset — nothing more.
In a real environment, this logic would move to a proper ingestion pipeline with:

Validation layers.

Retry policies.

and much more!

Please, treat load_data.py as a throwaway seed tool — not a production ingestion process.




## Notes
- SQLite DB is ephemeral unless you mount a Docker volume.
- Ensure the `tp_reviews.csv` file is present in the root directory before running the application.
- the `LOAD_DATA` environment variable controls whether the data ingestion script runs on startup.`LOAD_DATA=1` → runs ingestion on startup.

- the `USE_ALEMBIC` environment variable controls whether Alembic migrations are applied on startup. `USE_ALEMBIC=1` → applies migrations on startup.

- The subsequent run of the data ingestion script will not duplicate existing records due to the use of `INSERT ... ON CONFLICT`.
- ⚠️ **Alert!** the docker image is not pushed to any registry; it is built locally using the provided Makefile.
- ⚠️ **Alert!** the database is not persisted in the Docker container unless a volume is mounted.
- ⚠️ **Alert!** Subsequent run of the docker image by specifying LOAD_DATA=0 will skip the data ingestion step. But the database will be empty unless a volume is mounted to persist it.

## Testing

This project includes a comprehensive test suite to ensure the API endpoints and data processing logic function correctly. The tests are built using `pytest` and are designed to be fast and isolated from the production environment.

### Testing Strategy

-   **API Endpoint Testing (`tests/test_main.py`)**: The core API endpoints are tested to verify their behavior, status codes, and response formats.
-   **Database Isolation**: Tests use a separate, in-memory SQLite database for each test function. This is managed by fixtures in `tests/conftest.py`, which ensures that tests are completely isolated, do not interfere with each other, and do not require a running production database.
-   **Dependency Override**: The test setup correctly overrides the application's database session (`main.SessionLocal`) to point to the in-memory test database, ensuring API calls within tests use the isolated environment.
-   **Data Logic Testing (`test_load_data.py`)**: The data cleaning and upsert logic within `load_data.py` is tested to ensure it correctly processes, cleans, and prepares data for the database.

### How to Run Tests

1.  **Install Dependencies**:
    Make sure you have installed the project and test dependencies.

    ```bash
    pip install -r requirements.txt
    pip install pytest httpx
    ```

2.  **Execute the Test Suite**:
    From the root directory of the project, run `pytest`.

    ```bash
    pytest -v
    ```

    The `-v` flag provides a more verbose output, showing which tests passed. All tests should , hopefully,  pass :) ( it worked on my machine!!!), confirming that the application is working as expected.



## Path to Production

While this PoC effectively demonstrates core functionality, transitioning to a production environment requires significant enhancements for reliability, security, and scalability. The following steps outline a strategic path forward.

### 1. Decouple Application Startup from One-Off Tasks

The `entrypoint.sh` script currently handles database migrations and data loading. This is a critical anti-pattern for production as it makes application startup slow and fragile.

-   **Separate Database Migrations**: Migrations (`alembic upgrade head`) must be an explicit, separate step within a deployment pipeline, executed *before* the new application version is deployed. A failed migration should not prevent the application from starting.
-   **Externalize Data Ingestion**: The `load_data.py` script should be refactored into a standalone process (e.g., a scheduled job, a CLI command, or a message queue worker). The API server's sole responsibility should be serving requests.

### 2. Harden the Infrastructure and Database

-   **Use a Production-Grade Database**: Replace SQLite with a robust, concurrent database system like **PostgreSQL**. This is essential for handling multiple simultaneous connections and ensuring data integrity.
-   **Implement Asynchronous Database Calls**: To leverage FastAPI's async capabilities and prevent I/O blocking, refactor database logic in `main.py` to use an async driver (e.g., `asyncpg` for PostgreSQL) with SQLAlchemy's `AsyncSession`.
-   **Manage Secrets Securely**: Move database credentials and other secrets out of environment variables and into a dedicated secret management service (e.g., HashiCorp Vault, AWS Secrets Manager).

### 3. Enhance Observability

-   **Implement Structured Logging**: Convert the basic logging to a structured format (like JSON). This enables effective parsing and analysis in log aggregation platforms (e.g., Datadog, ELK Stack).
-   **Add a Health Check Endpoint**: Introduce a `/health` endpoint that can verify application status and database connectivity. This is crucial for load balancers and container orchestrators to manage application health.

### 4. Automate Deployment with a CI/CD Pipeline

-   **Build a CI/CD Pipeline**: Create a formal pipeline (e.g., using GitHub Actions) to automate linting, testing, building, and pushing the Docker image to a container registry (e.g., Docker Hub, ECR).
-   **Deploy to a Container Orchestrator**: Use a system like **Kubernetes** or **Amazon ECS** to manage deployments, enabling automated scaling, self-healing, and zero-downtime updates.


