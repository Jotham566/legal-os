from __future__ import annotations

import pytest

from legal_os.settings import Settings


def test_flags_nested_env_parsing(monkeypatch):
    monkeypatch.setenv("FLAGS__ENABLE_PGVECTOR", "true")
    s = Settings()
    assert s.flags.enable_pgvector is True


def test_production_requires_non_sqlite_and_no_debug(monkeypatch):
    # prod + sqlite should fail
    with pytest.raises(ValueError):
        Settings(
            env="production",
            debug=False,
            database_url="sqlite+pysqlite:///./x.db",
        ).assert_valid()

    # prod + debug=true should fail
    with pytest.raises(ValueError):
        Settings(
            env="production",
            debug=True,
            database_url="postgresql+psycopg://u:p@localhost/db",
        ).assert_valid()

    # valid production config should pass
    Settings(
        env="production",
        debug=False,
        database_url="postgresql+psycopg://u:p@localhost/db",
        jwt_secret="test-secret",
    ).assert_valid()


def test_pgvector_requires_postgres(monkeypatch):
    # enabling pgvector on sqlite should fail
    s = Settings(database_url="sqlite+pysqlite:///./x.db")
    s.flags.enable_pgvector = True
    with pytest.raises(ValueError):
        s.assert_valid()
