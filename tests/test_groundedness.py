from __future__ import annotations

from fastapi.testclient import TestClient

from legal_os.main import create_app


def make_client():
    app = create_app()
    return TestClient(app)


def test_groundedness_exact_match_passes():
    client = make_client()
    src = "Section 15. Digital services tax shall be imposed at 5% on gross receipts."
    ex = "digital services tax shall be imposed at 5% on gross receipts."
    res = client.post("/groundedness/verify", json={"extracted_text": ex, "source_text": src})
    assert res.status_code == 200
    payload = res.json()
    # Exact text match should normalize to 1.0 match ratio
    assert payload["checks"]["exact_text_match"] >= 0.995
    assert payload["overall"] >= 0.99
    assert payload["requires_re_extraction"] in (True, False)


def test_groundedness_number_and_date_precision():
    client = make_client()
    src = "On 10 July 2024, a tax of 5% shall apply as per Section 15."
    ex = "a tax of 5% shall apply on 10 July 2024"
    res = client.post("/groundedness/verify", json={"extracted_text": ex, "source_text": src})
    assert res.status_code == 200
    payload = res.json()
    assert payload["checks"]["numbers_precision"] == 1.0
    assert payload["checks"]["dates_precision"] == 1.0


def test_groundedness_cross_reference_detection():
    client = make_client()
    src = "See Section 2 and Part IV for more information."
    ex = "See Section 2"
    res = client.post("/groundedness/verify", json={"extracted_text": ex, "source_text": src})
    assert res.status_code == 200
    payload = res.json()
    assert payload["checks"]["cross_reference_integrity"] == 1.0
