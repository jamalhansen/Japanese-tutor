import pytest
from src.japanese_tutor.db import Database

@pytest.fixture
def db(tmp_path):
    db_file = tmp_path / "test.db"
    return Database(db_file)

def test_populate_and_due(db):
    chars = [{"char": "あ", "romaji": "a", "stage": "hiragana"}]
    db.populate_characters(chars)
    due = db.get_due_cards()
    assert len(due) == 1
    assert due[0]["character"] == "あ"
    assert due[0]["romaji_visible"] == 1

def test_romaji_fading(db):
    chars = [{"char": "あ", "romaji": "a", "stage": "hiragana"}]
    db.populate_characters(chars)
    card_id = db.get_due_cards()[0]["card_id"]
    
    # 5 consecutive correct
    for _ in range(5):
        db.update_card(card_id, 5, 1, 1, 2.5)
        
    card = db.get_card(card_id)
    assert card["romaji_visible"] == 0
    
    # One fail brings it back
    db.update_card(card_id, 0, 1, 0, 2.4)
    card = db.get_card(card_id)
    assert card["romaji_visible"] == 1
