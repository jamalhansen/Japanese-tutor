from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from japanese_tutor import api

client = TestClient(api.app)

@pytest.fixture
def mock_state():
    api.db = MagicMock()
    api.llm_helper = MagicMock()
    yield
    api.db = None
    api.llm_helper = None

def test_get_due_cards(mock_state):
    api.db.is_stage_mastered.return_value = False
    api.db.get_due_cards.return_value = [{"id": 1, "char": "あ"}]
    
    response = client.get("/api/cards/due")
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "char": "あ"}]
    api.db.get_due_cards.assert_called_with(stage="hiragana", practice=False)

def test_get_due_cards_practice(mock_state):
    api.db.is_stage_mastered.return_value = False
    api.db.get_due_cards.return_value = [{"id": 1, "char": "あ"}]
    
    response = client.get("/api/cards/due?practice=true")
    assert response.status_code == 200
    api.db.get_due_cards.assert_called_with(stage="hiragana", practice=True)

def test_submit_review(mock_state):
    api.db.get_card.return_value = {
        "id": 1, "repetitions": 0, "interval_days": 0, "easiness_factor": 2.5
    }
    
    response = client.post("/api/reviews", json={"card_id": 1, "rating": 4})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    api.db.update_card.assert_called_once()

def test_get_mastery(mock_state):
    api.db.get_mastery_stats.return_value = {"hiragana": 0.5}
    response = client.get("/api/mastery")
    assert response.status_code == 200
    assert response.json() == {"hiragana": 0.5}

def test_get_example(mock_state):
    api.llm_helper.generate_adaptive_example.return_value = "Example sentence"
    response = client.get("/api/example/あ")
    assert response.status_code == 200
    assert response.json() == {"example": "Example sentence"}

def test_mnemonics(mock_state):
    api.llm_helper.generate_mnemonics.return_value = ["Mnemonic 1"]
    response = client.post("/api/mnemonics/generate", json={"character": "あ", "romaji": "a"})
    assert response.status_code == 200
    assert response.json() == {"suggestions": ["Mnemonic 1"]}


# --- Rating validation ---

def test_submit_review_invalid_rating_too_high(mock_state):
    response = client.post("/api/reviews", json={"card_id": 1, "rating": 6})
    assert response.status_code == 422


def test_submit_review_invalid_rating_negative(mock_state):
    response = client.post("/api/reviews", json={"card_id": 1, "rating": -1})
    assert response.status_code == 422


# --- Session endpoints ---

def test_start_session(mock_state):
    api.db.start_session.return_value = 42
    response = client.post("/api/session/start", json={"stage": "hiragana"})
    assert response.status_code == 200
    assert response.json() == {"session_id": 42}
    api.db.start_session.assert_called_once_with(stage="hiragana", provider=None, model=None)


def test_end_session(mock_state):
    response = client.post("/api/session/end/42")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    api.db.end_session.assert_called_once_with(42)


def test_get_sessions(mock_state):
    api.db.get_sessions.return_value = [{"id": 1, "cards_reviewed": 5}]
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert response.json()[0]["id"] == 1


def test_get_session_detail(mock_state):
    api.db.get_session.return_value = {"id": 1, "cards_reviewed": 5, "reviews": []}
    response = client.get("/api/sessions/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_session_not_found(mock_state):
    api.db.get_session.return_value = None
    response = client.get("/api/sessions/9999")
    assert response.status_code == 404


def test_submit_review_updates_session(mock_state):
    api.db.get_card.return_value = {
        "id": 1, "repetitions": 0, "interval_days": 0, "easiness_factor": 2.5
    }
    response = client.post("/api/reviews", json={"card_id": 1, "rating": 4, "session_id": 7})
    assert response.status_code == 200
    api.db.update_session_stats.assert_called_once_with(7, 4)
