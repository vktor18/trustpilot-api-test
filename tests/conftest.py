import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models import Base
import main

@pytest.fixture(scope="session")
def engine():
    """
    Create a single in-memory SQLite engine for the whole test session.
    Using StaticPool ensures the same in-memory DB is reused across connections.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # create all tables once for the test session
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """
    Create a connection + transaction per test and bind a sessionmaker to that connection.
    We temporarily override main.SessionLocal so the app uses the test sessionmaker.
    After the test we rollback the transaction to keep tests isolated.
    """
    # new connection + transaction (so we can rollback after test)
    connection = engine.connect()
    transaction = connection.begin()

    # sessionmaker bound to *this* connection
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)

    # override main.SessionLocal for the duration of this test
    original_sessionlocal = getattr(main, "SessionLocal", None)
    main.SessionLocal = TestingSessionLocal

    # create a session instance for the test to use directly
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # cleanup: close session, rollback transaction, close connection, restore main.SessionLocal
        session.close()
        transaction.rollback()
        connection.close()
        main.SessionLocal = original_sessionlocal
