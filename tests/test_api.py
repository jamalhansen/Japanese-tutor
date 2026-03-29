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
