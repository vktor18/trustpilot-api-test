#!/usr/bin/env sh
set -e

# This script serves as the entrypoint for the Trustpilot PoC API container.
# It ensures Alembic migrations are initialized and applied, optionally loads data from CSV,
# and finally starts the FastAPI application using Uvicorn.

# Check if Alembic is initialized; if not, initialize it.
if [ ! -d "alembic" ] || [ ! -d "alembic/versions" ]; then
  echo "Alembic not initialized. Initializing Alembic..."
  alembic init alembic || true
fi

# If USE_ALEMBIC=1, apply migrations.
if [ "${USE_ALEMBIC}" = "1" ]; then
  if command -v alembic >/dev/null 2>&1; then
    if [ -z "$(find alembic/versions -type f 2>/dev/null)" ]; then
      echo "No Alembic migrations found. Creating the first migration..."
      alembic revision --autogenerate -m "Initial migration" || { echo "Failed to create initial migration"; exit 1; }
    fi
    echo "Applying Alembic migrations..."
    alembic upgrade head || { echo "Failed to apply migrations"; exit 1; }
  else
    echo "Alembic is not installed. Skipping migrations."
  fi
else
  echo "USE_ALEMBIC is not set to 1. Skipping migrations."
fi

# If LOAD_DATA=1, load data into the database.
if [ "${LOAD_DATA}" = "1" ]; then
  echo "Loading initial data..."
  if ! python load_data.py; then
    echo "Failed to load data."
    exit 1
  fi
else
  echo "LOAD_DATA is not set to 1. Skipping data load."
fi

# Start the FastAPI application using Uvicorn.
echo "Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
