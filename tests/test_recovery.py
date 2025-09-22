from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from legal_os.main import app
from legal_os.services.recovery import LegalErrorRecoverySystem


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_recover_poor_scan_triggers_ocr():
    system = LegalErrorRecoverySystem()
    # Very low text-like ratio simulating binary/scan
    data = b"\x00\x01\x02 corrupted \x03\x04"
    report = system.recover(data, base_confidence=0.5)
    assert any(
        s.step == "enhanced_ocr" and s.applied for s in report.applied_strategies
    )
    assert report.confidence_after >= 0.75 or report.recovered is True


def test_recover_complex_table_triggers_table_extraction():
    system = LegalErrorRecoverySystem()
    text = "| col1 | col2 |\n|------|------|\nSection 1"
    report = system.recover(text.encode("utf-8"), base_confidence=0.5)
    assert any(
        s.step == "table_extraction" and s.applied for s in report.applied_strategies
    )


def test_recovery_endpoint_success(client):
    files = {"file": ("scan.pdf", b"\x00\x00 binary ", "application/pdf")}
    res = client.post("/error-recovery/attempt", files=files)
    assert res.status_code == 200
    body = res.json()
    assert "recovered" in body and "applied_strategies" in body


def test_recovery_endpoint_empty_file(client):
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    res = client.post("/error-recovery/attempt", files=files)
    assert res.status_code == 400
