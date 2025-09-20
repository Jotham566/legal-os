from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.engine import Engine

from .settings import get_settings


Base = declarative_base()


def get_engine(echo: bool | None = None) -> Engine:
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        echo=settings.debug if echo is None else echo,
        future=True,
    )
    return engine


def ping_database() -> bool:
    """Perform a lightweight connectivity check against the configured DB.

    Returns True if a simple SELECT 1 executes successfully, otherwise False.
    """
    try:
        engine = get_engine(echo=False)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


# Configure a session factory (synchronous)
SessionLocal = sessionmaker(
    bind=get_engine(),
    autoflush=False,
    autocommit=False,
    future=True,
    expire_on_commit=False,
)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session: Session = SessionLocal()  # type: ignore[call-arg]
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
