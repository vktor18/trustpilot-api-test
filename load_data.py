import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from models import Base, TPReview

# Configure logging for the module
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///trustpilot_test.db")
USE_ALEMBIC = os.getenv("USE_ALEMBIC", "0") == "1"


def _engine_for_url(url: str):
    """
    Create a SQLAlchemy engine for the given database URL.

    Args:
        url (str): Database connection URL.

    Returns:
        sqlalchemy.engine.Engine: SQLAlchemy engine instance.
    """
    # Use 'check_same_thread' for SQLite to allow usage in multi-threaded environments
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the input DataFrame by removing duplicates, filtering invalid dates and ratings.

    Steps:
        - Remove duplicate reviews based on 'Review_Id'.
        - Convert 'Review_Date' to datetime, dropping rows with invalid dates.
        - Convert 'Review_Rating' to numeric, keeping only ratings between 1 and 5.

    Args:
        df (pd.DataFrame): Raw DataFrame loaded from CSV.

    Returns:
        pd.DataFrame: Cleaned DataFrame ready for database insertion.
    """
    logging.info("Starting data cleaning process.")
    # Remove duplicate reviews by 'Review_Id'
    df = df.drop_duplicates(subset=["Review_Id"], keep="first")
    logging.info(f"Removed duplicates. Remaining rows: {len(df)}")
    # Convert 'Review_Date' to datetime and drop rows with invalid dates
    df["Review_Date"] = pd.to_datetime(df["Review_Date"], errors="coerce")
    df = df.dropna(subset=["Review_Date"])
    logging.info(f"Filtered invalid dates. Remaining rows: {len(df)}")
    # Convert 'Review_Rating' to numeric and filter for valid ratings (1-5)
    #df["Review Rating"] = pd.to_numeric(df["Review_Rating"], errors="coerce")
    df = df[df["Review_Rating"].apply(lambda x: isinstance(x, (int, float)) and 1 <= x <= 5)]
    #df = df[(df["Review_Rating"] >= 1) & (df["Review_Rating"] <= 5)]
    logging.info(f"Filtered invalid ratings. Remaining rows: {len(df)}")
    return df


def upsert_records(engine, records: list, dialect: str = "sqlite", batch_size: int = 500):
    """
    Upsert (insert or update) records into the database in batches.

    Uses dialect-specific SQLAlchemy insert functions to perform upserts.
    For SQLite, uses 'on_conflict_do_update' on 'Review_Id'.
    For PostgreSQL, uses 'on_conflict_do_update' on 'Review_Id'.

    Args:
        engine: SQLAlchemy engine instance.
        records (list): List of dictionaries representing review records.
        dialect (str): Database dialect ('sqlite' or 'postgres').
        batch_size (int): Number of records per batch.

    Returns:
        None

    Side Effects:
        Writes records to the database.
    """
    table = TPReview.__table__
    insert_fn = sqlite_insert if dialect.startswith("sqlite") else pg_insert
    # Prepare columns for update, excluding the primary key
    cols = [c.name for c in table.columns if c.name != "Review_Id"]

    # Process records in batches for efficiency
    with engine.begin() as conn:
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            logging.info(f"Processing batch {i // batch_size + 1} of {len(records) // batch_size + 1}")
            ins = insert_fn(table)
            # Map columns to their excluded values for upsert
            update_map = {c: getattr(ins.excluded, c) for c in cols}
            stmt = ins.on_conflict_do_update(index_elements=["Review_Id"], set_=update_map)
            conn.execute(stmt, batch)
            logging.info(f"Upserted {len(batch)} records.")


def load_csv_to_db(csv_path: str = "tp_reviews.csv") -> None:
    """
    Load reviews from a CSV file, clean the data, and upsert into the database.

    Args:
        csv_path (str): Path to the CSV file containing reviews.

    Returns:
        None

    Side Effects:
        Reads from CSV, writes to database, logs progress.
    """
    try:
        logging.info(f"Loading CSV file: {csv_path}")
        # Read CSV and rename columns to match database schema
        df = pd.read_csv(csv_path)
        df.rename(columns={
            "Review Id": "Review_Id",
            "Reviewer Name": "Reviewer_Name",
            "Review Title": "Review_Title",
            "Review Rating": "Review_Rating",
            "Review Content": "Review_Content",
            "Review IP Address": "Review_IP_Address",
            "Business Id": "Business_Id",
            "Business Name": "Business_Name",
            "Reviewer Id": "Reviewer_Id",
            "Email Address": "Email_Address",
            "Reviewer Country": "Reviewer_Country",
            "Review Date": "Review_Date"
        }, inplace=True)
    except Exception as e:
        logging.error(f"Failed to read CSV file {csv_path}: {e}")
        return

    # Clean the loaded data
    df = clean_data(df)
    print(df)  # For debugging: print cleaned DataFrame
    logging.info(f"Processing {len(df)} cleaned rows for upsert...")

    # Create database engine
    engine = _engine_for_url(DATABASE_URL)

    # Convert DataFrame to list of dicts for upsert
    records = df.to_dict(orient="records")
    print("this is the records")  # For debugging: print records list
    print(records)
    dialect = "sqlite" if DATABASE_URL.startswith("sqlite") else "postgres"

    try:
        # Upsert records into the database
        upsert_records(engine, records, dialect=dialect)
        logging.info(f"Successfully upserted {len(records)} rows into the database.")
        # Query and log total row count in the database
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM tp_reviews")).scalar()
            logging.info(f"Total rows in the database: {count}")
    except Exception as e:
        logging.error(f"Error during data ingestion: {e}")
        raise


if __name__ == "__main__":
    """
    Script entry point. Creates database tables if Alembic is not used,
    then loads and ingests data from the CSV file.
    """
    engine = _engine_for_url(DATABASE_URL)
    # Create tables if Alembic migrations are not used
    if not USE_ALEMBIC:
        Base.metadata.create_all(bind=engine)
    # Load and ingest data from CSV
    load_csv_to_db("tp_reviews.csv")