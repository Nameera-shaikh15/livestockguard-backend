import pytest
from app.database.database import init_db, engine, Base


@pytest.fixture(autouse=True, scope="session")
def setup_test_database():
    """Ensure SQLite database schema and tables are created before running tests."""
    init_db()
    yield
