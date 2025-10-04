# Trustpilot PoC API

## Overview
This project is a Proof of Concept (PoC) API designed to handle and serve Trustpilot review data. It ingests a mock dataset of Trustpilot reviews from a CSV file into a database, cleans the data, and provides RESTful API endpoints to retrieve the data in JSON or CSV format. The API is built using FastAPI and supports efficient streaming of large datasets.

## Features
- **Data Ingestion**: Load and clean a CSV file (`tp_reviews.csv`) into an SQLite database.
- **Data Cleaning**:
  - Remove duplicate reviews.
  - Validate and normalize review dates.
  - Ensure ratings are within the valid range (1-5).
- **API Endpoints**:
  - `/business/{business_id}/reviews`: Retrieve reviews for a specific business.
  - `/user/{reviewer_id}/reviews`: Retrieve reviews written by a specific user.
  - `/user/{reviewer_id}/account`: Retrieve user account information.
- **Streaming Responses**: Efficiently stream large CSV files for endpoints that return bulk data.
- **Idempotent Ingestion**: Avoid duplicate entries in the database using `INSERT ... ON CONFLICT`.
- **Dockerized Setup**: Easily run the application in a containerized environment.
- **Makefile Commands**: Simplify build, run, and clean operations.

## Requirements
- Python 3.11+
- SQLite (default database)
- Dependencies listed in `requirements.txt`
- Docker (optional, for containerized setup)

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

## Notes
- The SQLite database is ephemeral unless a volume is mounted when using Docker. To persist data, map the database file to a local directory.
- Ensure the `tp_reviews.csv` file is present in the root directory before running the application.
- the `LOAD_DATA` environment variable controls whether the data ingestion script runs on startup.
- the `USE_ALEMBIC` environment variable controls whether Alembic migrations are applied on startup.
- The subsequent run of the data ingestion script will not duplicate existing records due to the use of `INSERT ... ON CONFLICT`.
- ⚠️ **Alert!** the docker image is not pushed to any registry; it is built locally using the provided Makefile.
- ⚠️ **Alert!** the database is not persisted in the Docker container unless a volume is mounted.
- ⚠️ **Alert!** Subsequent run of the docker image by specifying LOAD_DATA=0 will skip the data ingestion step. But the database will be empty unless a volume is mounted to persist it.