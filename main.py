import os
import csv
import io
import logging
from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from models import TPReview
from typing import Generator

# Configure logging for the application
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///trustpilot_test.db")


def _engine_for_url(url: str):
    """
    Create a SQLAlchemy engine for the given database URL.

    Args:
        url (str): Database connection URL.

    Returns:
        sqlalchemy.engine.Engine: SQLAlchemy engine instance.
    """
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = _engine_for_url(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

# Initialize FastAPI application
app = FastAPI(title="Trustpilot PoC API")

# List of columns to include in CSV output
CSV_COLUMNS = [
    "Review_Id",
    "Reviewer_Name",
    "Review_Title",
    "Review_Rating",
    "Review_Content",
    "Review_IP_Address",
    "Business_Id",
    "Business_Name",
    "Reviewer_Id",
    "Email_Address",
    "Reviewer_Country",
    "Review_Date",
]


def stream_rows_for_stmt(stmt) -> Generator[str, None, None]:
    """
    Stream rows from the database as CSV, keeping the session open during streaming.

    Args:
        stmt: SQLAlchemy select statement.

    Yields:
        str: CSV-formatted string for each row.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # Write CSV header
    writer.writerow(CSV_COLUMNS)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    session = SessionLocal()
    try:
        logging.info("Executing query for streaming rows.")
        scalar_result = session.execute(stmt).scalars()
        for r in scalar_result:
            # Extract values for each column, defaulting to empty string if missing
            row = [getattr(r, col, "") for col in CSV_COLUMNS]
            writer.writerow(row)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
    except Exception as e:
        logging.error(f"Error during streaming rows: {e}")
        raise
    finally:
        session.close()
        logging.info("Database session closed after streaming.")


@app.get("/")
def read_root():
    """
    Root endpoint providing a welcome message.

    Returns:
        dict: Welcome message.
    """
    return {"message": "Welcome to the Trustpilot API!"}


@app.get("/business/{business_id}/reviews")
def business_reviews_csv(business_id: str):
    """
    Endpoint to stream all reviews for a specific business as a CSV file.

    Args:
        business_id (str): Unique identifier for the business.

    Returns:
        StreamingResponse: CSV file containing all reviews for the business.
    """
    logging.info(f"Received request for business reviews: business_id={business_id}")
    stmt = select(TPReview).where(TPReview.Business_Id == business_id)
    generator = stream_rows_for_stmt(stmt)
    headers = {"Content-Disposition": f'attachment; filename="{business_id}_reviews.csv"'}
    return StreamingResponse(generator, media_type="text/csv", headers=headers)


@app.get("/user/{reviewer_id}/reviews")
def user_reviews_csv(reviewer_id: str):
    """
    Endpoint to stream all reviews written by a specific user as a CSV file.

    Args:
        reviewer_id (str): Unique identifier for the reviewer.

    Returns:
        StreamingResponse: CSV file containing all reviews by the user.
    Raises:
        HTTPException: If no reviews are found for the given reviewer_id.
    """
    logging.info(f"Received request for user reviews: reviewer_id={reviewer_id}")
    session = SessionLocal()
    try:
        # Check if any reviews exist for the given reviewer_id
        stmt = select(TPReview).where(TPReview.Reviewer_Id == reviewer_id)
        exists = session.execute(stmt).scalars().first()
        if not exists:
            logging.warning(f"No reviews found for reviewer_id={reviewer_id}")
            raise HTTPException(status_code=404, detail="No reviews found for the given reviewer_id")

        # Stream the reviews as CSV
        generator = stream_rows_for_stmt(stmt)
        headers = {"Content-Disposition": f'attachment; filename="{reviewer_id}_reviews.csv"'}
        return StreamingResponse(generator, media_type="text/csv", headers=headers)
    finally:
        session.close()


@app.get("/user/{reviewer_id}/account")
def user_account_info(reviewer_id: str):
    """
    Endpoint to fetch basic account information for a user.

    Args:
        reviewer_id (str): Unique identifier for the reviewer.

    Returns:
        JSONResponse: Basic account info for the user.
    Raises:
        HTTPException: If the user is not found.
    """
    logging.info(f"Received request for user account info: reviewer_id={reviewer_id}")
    try:
        with SessionLocal() as session:
            stmt = select(TPReview).where(TPReview.Reviewer_Id == reviewer_id)
            first = session.execute(stmt).scalars().first()
            if not first:
                logging.warning(f"User not found: reviewer_id={reviewer_id}")
                raise HTTPException(status_code=404, detail="Reviewer not found")
            account = {
                "Reviewer_Id": first.Reviewer_Id,
                "Reviewer_Name": first.Reviewer_Name,
                "Email_Address": first.Email_Address,
                "Reviewer_Country": first.Reviewer_Country,
            }
            logging.info(f"Returning account info for reviewer_id={reviewer_id}")
            return JSONResponse(content=account)
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching user account info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
