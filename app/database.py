from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def _engine_url() -> str:
    url = settings.resolved_database_url
    if url.startswith("sqlite:"):
        Path(url.replace("sqlite:///", "").split("?")[0]).parent.mkdir(parents=True, exist_ok=True)
    return url


engine = create_engine(
    _engine_url(),
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if settings.resolved_database_url.startswith("sqlite:") else {},
)
if settings.resolved_database_url.startswith("sqlite:"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
