from pathlib import Path

from sqlmodel import Session, create_engine

from config import get_settings

settings = get_settings()

DATABASE_PATH = Path(settings.JOBS_DB)
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
CONNECT_ARGS = {"check_same_thread": False}


engine = create_engine(DATABASE_URL, echo=False, connect_args=CONNECT_ARGS)


def get_db():
    # Create a SQLModel Session instance directly
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
