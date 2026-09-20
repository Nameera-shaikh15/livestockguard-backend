from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# SQLite requires check_same_thread=False for multi-threaded FastAPI access
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import all models to ensure they register with Base.metadata before creating tables
    import app.models.animal  # noqa: F401
    import app.models.analysis  # noqa: F401
    import app.models.alert  # noqa: F401
    Base.metadata.create_all(bind=engine)
