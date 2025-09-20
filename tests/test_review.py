from __future__ import annotations

from fastapi.testclient import TestClient

from legal_os.main import create_app


def make_client():
    app = create_app()
    return TestClient(app)


def test_review_route_creates_task_on_low_confidence():
    client = make_client()
    body = {
        "final_confidence": 0.84,
        "contains_constitutional": False,
        "contains_tax": False,
        "contains_commercial": False,
        "has_complex_refs": True,
        "involves_definitions": True,
    }
    res = client.post("/review/assess-route", json=body)
    assert res.status_code == 200
    payload = res.json()
    assert payload["task_id"] is not None
    assert "confidence_below_85" in payload["reasons"]

    # List and progress task
    res2 = client.get("/review/tasks")
    assert res2.status_code == 200
    tasks = res2.json()
    assert len(tasks) >= 1
    task_id = payload["task_id"]

    res3 = client.post(f"/review/tasks/{task_id}/start")
    assert res3.status_code == 200

    res4 = client.post(f"/review/tasks/{task_id}/complete", json={"accepted": True})
    assert res4.status_code == 200


def test_review_no_task_when_high_confidence():
    client = make_client()
    body = {
        "final_confidence": 0.99,
        "contains_constitutional": False,
        "contains_tax": False,
        "contains_commercial": False,
        "has_complex_refs": False,
        "involves_definitions": False,
    }
    res = client.post("/review/assess-route", json=body)
    assert res.status_code == 200
    payload = res.json()
    assert payload["task_id"] is None
    assert payload["reasons"] == []
