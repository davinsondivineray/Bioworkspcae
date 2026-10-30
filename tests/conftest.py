import os

os.environ["APP_ENV"] = "test"
os.environ["DEV_AUTH"] = "true"
os.environ["DATABASE_URL"] = "sqlite:////tmp/biotech-platform-test-global.sqlite3"
os.environ["LOCAL_UPLOAD_DIR"] = "/tmp/biotech-platform-test-uploads"
os.environ["IDENTIFIABLE_RECORDS_ENABLED"] = "false"
os.environ["AI_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models  # noqa: F401


test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


def override_get_db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
