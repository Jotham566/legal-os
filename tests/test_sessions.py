from __future__ import annotations

from fastapi.testclient import TestClient

from legal_os.main import create_app
from legal_os.db import get_engine, Base


def test_create_get_update_complete_session():
    # Ensure tables exist for this test
    engine = get_engine(echo=False)
    Base.metadata.create_all(bind=engine)

    app = create_app()
    client = TestClient(app)

    # create
    resp = client.post("/sessions/", json={"source_key": "uploads/hash.pdf"})
    assert resp.status_code == 200
    created = resp.json()
    sid = created["id"]
    assert created["status"] == "running"
    assert created["progress"] == 0

    # get
    resp = client.get(f"/sessions/{sid}")
    assert resp.status_code == 200

    # update progress and checkpoint
    resp = client.patch(
        f"/sessions/{sid}",
        json={"progress": 50, "eta_seconds": 120, "checkpoint": {"stage": "uploaded"}},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["progress"] == 50
    assert updated["eta_seconds"] == 120
    assert updated["checkpoints"]["stage"] == "uploaded"

    # complete
    resp = client.patch(f"/sessions/{sid}", json={"status": "completed", "progress": 100})
    assert resp.status_code == 200
    done = resp.json()
    assert done["status"] == "completed"
    assert done["progress"] == 100
