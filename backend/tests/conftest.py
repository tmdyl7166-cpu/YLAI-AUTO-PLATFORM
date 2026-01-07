"""Pytest configuration and fixtures for backend tests."""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Use test database URL from environment or default to SQLite in-memory
TEST_DB_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///:memory:"
)


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False} if "sqlite" in TEST_DB_URL else {},
        echo=False
    )
    # Create all tables (assumes Base.metadata is defined in backend.models)
    # from backend.models import Base
    # Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine):
    """Create a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from backend.app import app
    with TestClient(app) as client:
        yield client


@pytest.fixture
def redis_client():
    """Create a test Redis client (optional mock)."""
    # For CI, use fakeredis; for local, use real Redis if available
    try:
        import redis
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/1")
        return redis.from_url(redis_url)
    except Exception:
        # Fallback to fakeredis if redis unavailable
        try:
            import fakeredis
            return fakeredis.FakeStrictRedis()
        except ImportError:
            return None


@pytest.fixture
def sample_token(test_client):
    """Get a sample auth token for tests (if auth is implemented)."""
    try:
        response = test_client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception:
        pass
    return None
