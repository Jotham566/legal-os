import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from legal_os.services.citation import CitationService, Citation
import logging


@pytest.fixture
def client():
    from legal_os.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_session():
    return {"user_id": "test_user", "document_id": "test_doc"}


def test_extract_citations(mock_session):
    service = CitationService(mock_session)
    text = "Section 123 of Income Tax Act. Article 45 of Constitution."
    citations = service.extract_citations(text)
    assert len(citations) >= 1
    assert any("Section 123" in cit.text for cit in citations)
    assert all(cit.confidence >= 0.995 for cit in citations)


def test_validate_accuracy(mock_session):
    service = CitationService(mock_session)
    cit = Citation(
        text="Section 123 of Income Tax Act",
        section="123",
        page=1,
        char_offset=0,
        coordinates=(0, 0, 0, 0),
        confidence=0.995,
    )
    assert service.validate_accuracy(cit, "Section 123 of Income Tax Act")
    assert not service.validate_accuracy(cit, "Wrong Section")


def test_ground_coordinates(mock_session):
    service = CitationService(mock_session)
    cit = Citation(
        text="Test",
        section="test",
        page=1,
        char_offset=10,
        coordinates=(0, 0, 0, 0),
        confidence=0.995,
    )
    grounded = service.ground_coordinates(cit, "/mock.pdf", "Line1\nLine2 Test")
    assert grounded.coordinates != (0, 0, 0, 0)  # Should be mocked non-zero
    assert isinstance(grounded.coordinates, tuple) and len(grounded.coordinates) == 4


def test_format_citation(mock_session):
    service = CitationService(mock_session)
    cit = Citation(
        text="Income Tax Act",
        section="123",
        page=1,
        char_offset=0,
        coordinates=(0, 0, 0, 0),
        confidence=0.995,
    )
    formatted = service.format_citation(cit)
    assert "§ 123" in formatted  # Bluebook style
    assert "(p. 1)" in formatted or "Income Tax Act" in formatted


def test_log_audit_trail(mock_session, caplog):
    service = CitationService(mock_session)
    cit = Citation(
        text="Test Citation",
        section="test",
        page=1,
        char_offset=0,
        coordinates=(0, 0, 0, 0),
        confidence=0.995,
    )
    service.log_audit_trail(cit, "test_op")
    assert any("test_op" in r.message for r in caplog.records)
    assert "Audit trail" in caplog.records[0].message


@patch('legal_os.routers.citation.mock_get_session')
def test_verify_citations_endpoint(mock_session, client, caplog):
    caplog.set_level(logging.WARNING, logger="httpx")
    mock_session.return_value = {"user_id": "test", "document_id": "doc1"}
    response = client.post(
        "/api/v1/citations/verify",
        json={
            "document_id": "doc1",
            "text": "Section 123 of Income Tax Act",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "citations" in data
    assert data["audit_trail_count"] >= 0


def test_accuracy_threshold(mock_session):
    service = CitationService(mock_session)
    cit_low = Citation(
        text="Low match",
        section="low",
        page=1,
        char_offset=0,
        coordinates=(0, 0, 0, 0),
        confidence=0.99,
    )
    assert not service.validate_accuracy(cit_low, "High match")  # Assuming low similarity
