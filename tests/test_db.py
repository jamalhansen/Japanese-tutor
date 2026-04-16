import pytest
from japanese_tutor.db import Database

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

def test_practice_mode(db):
    chars = [{"char": "あ", "romaji": "a", "stage": "hiragana"}]
    db.populate_characters(chars)
    
    # Manually update next_review_at to future
    with db._get_connection() as conn:
        conn.execute("UPDATE cards SET next_review_at = '2099-01-01T00:00:00'")
    
    # Not due
    due = db.get_due_cards()
    assert len(due) == 0
    
    # But available in practice mode
    practice = db.get_due_cards(practice=True)
    assert len(practice) == 1
    assert practice[0]["character"] == "あ"
