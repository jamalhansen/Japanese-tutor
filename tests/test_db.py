import pytest

from japanese_tutor.db import Database

CHARS = [{"char": "あ", "romaji": "a", "stage": "hiragana"}]


@pytest.fixture
def db(tmp_path):
    db_file = tmp_path / "test.db"
    return Database(db_file)


@pytest.fixture
def db_with_card(db):
    db.populate_characters(CHARS)
    return db


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

    # Non-practice mode now backfills with upcoming cards
    due = db.get_due_cards()
    assert len(due) == 1
    assert due[0]["character"] == "あ"

    # But available in practice mode
    practice = db.get_due_cards(practice=True)
    assert len(practice) == 1
    assert practice[0]["character"] == "あ"


def test_non_practice_backfills_to_limit(db):
    chars = [
        {"char": "あ", "romaji": "a", "stage": "hiragana"},
        {"char": "い", "romaji": "i", "stage": "hiragana"},
        {"char": "う", "romaji": "u", "stage": "hiragana"},
    ]
    db.populate_characters(chars)

    # Make only one card truly due; other cards are in the future.
    with db._get_connection() as conn:
        conn.execute(
            "UPDATE cards SET next_review_at = '2099-01-01T00:00:00' WHERE id != 1"
        )

    cards = db.get_due_cards(limit=3, practice=False)
    assert len(cards) == 3
    # Due card appears first, then backfilled upcoming cards.
    assert cards[0]["card_id"] == 1


def test_get_due_count_does_not_backfill(db):
    """Regression 2026-09-20: get_due_cards() pads its response up to
    `limit` with not-yet-due cards, so len(get_due_cards()) stays at `limit`
    regardless of how many are genuinely overdue -- a real dashboard bug
    where the "cards due" count never went down after reviewing several
    cards. get_due_count() is the true overdue count, no padding."""
    chars = [
        {"char": "あ", "romaji": "a", "stage": "hiragana"},
        {"char": "い", "romaji": "i", "stage": "hiragana"},
        {"char": "う", "romaji": "u", "stage": "hiragana"},
    ]
    db.populate_characters(chars)

    # Make only one card truly due; other cards are in the future.
    with db._get_connection() as conn:
        conn.execute(
            "UPDATE cards SET next_review_at = '2099-01-01T00:00:00' WHERE id != 1"
        )

    # get_due_cards() backfills to 3 (limit's default of 20, capped by deck size)
    assert len(db.get_due_cards()) == 3
    # get_due_count() reports the real number: 1
    assert db.get_due_count() == 1


def test_get_due_count_goes_to_zero_when_nothing_is_due(db_with_card):
    with db_with_card._get_connection() as conn:
        conn.execute("UPDATE cards SET next_review_at = '2099-01-01T00:00:00'")
    assert db_with_card.get_due_count() == 0


def test_get_due_count_respects_stage_filter(db):
    chars = [
        {"char": "あ", "romaji": "a", "stage": "hiragana"},
        {"char": "ア", "romaji": "a", "stage": "katakana"},
    ]
    db.populate_characters(chars)
    assert db.get_due_count(stage="hiragana") == 1
    assert db.get_due_count(stage="katakana") == 1
    assert db.get_due_count() == 2


def test_get_reviews_today_count_is_zero_with_no_reviews(db_with_card):
    counts = db_with_card.get_reviews_today_count()
    assert counts == {"attempts": 0, "distinct_cards": 0}


def test_get_reviews_today_count_counts_attempts_and_distinct_cards(db):
    """Regression 2026-09-20: due count alone couldn't explain why reviewing
    ~15 cards barely moved it -- attempts (every submission, including
    retries) vs distinct_cards (unique characters touched) is the real
    answer, and the two numbers together show it."""
    chars = [
        {"char": "あ", "romaji": "a", "stage": "hiragana"},
        {"char": "い", "romaji": "i", "stage": "hiragana"},
    ]
    db.populate_characters(chars)
    cards = db.get_due_cards()
    card_a, card_b = cards[0]["card_id"], cards[1]["card_id"]

    # Two attempts on the same card (a retry), one on another.
    db.update_card(card_a, 5, 1, 1, 2.5)
    db.update_card(card_a, 2, 1, 0, 2.4)
    db.update_card(card_b, 5, 1, 1, 2.5)

    counts = db.get_reviews_today_count()
    assert counts == {"attempts": 3, "distinct_cards": 2}


def test_get_reviews_today_count_excludes_reviews_from_before_local_midnight(
    db_with_card,
):
    card_id = db_with_card.get_due_cards()[0]["card_id"]
    db_with_card.update_card(card_id, 5, 1, 1, 2.5)

    # Backdate the just-inserted review to well before today.
    with db_with_card._get_connection() as conn:
        conn.execute(
            "UPDATE reviews SET reviewed_at = '2020-01-01T00:00:00+00:00' "
            "WHERE card_id = ?",
            (card_id,),
        )

    assert db_with_card.get_reviews_today_count() == {
        "attempts": 0,
        "distinct_cards": 0,
    }


# --- save_mnemonic idempotency ---


def test_save_mnemonic_idempotent(db_with_card):
    card_id = db_with_card.get_due_cards()[0]["card_id"]
    card = db_with_card.get_card(card_id)
    char_id = card["character_id"]

    db_with_card.save_mnemonic(char_id, "First mnemonic", source="manual")
    db_with_card.save_mnemonic(char_id, "Updated mnemonic", source="llm")

    with db_with_card._get_connection() as conn:
        rows = conn.execute(
            "SELECT body, source FROM associations WHERE character_id = ?", (char_id,)
        ).fetchall()
    assert len(rows) == 1
    assert rows[0]["body"] == "Updated mnemonic"
    assert rows[0]["source"] == "llm"


# --- Session management ---


def test_start_and_end_session(db):
    session_id = db.start_session(stage="hiragana", provider="local", model="phi4-mini")
    assert isinstance(session_id, int)

    sessions = db.get_sessions()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_id
    assert sessions[0]["ended_at"] is None

    db.end_session(session_id)
    sessions = db.get_sessions()
    assert sessions[0]["ended_at"] is not None


def test_update_session_stats(db):
    session_id = db.start_session(stage="hiragana")

    db.update_session_stats(session_id, rating=5)  # correct
    db.update_session_stats(session_id, rating=4)  # correct
    db.update_session_stats(session_id, rating=0)  # again

    session = db.get_session(session_id)
    assert session["cards_reviewed"] == 3
    assert session["correct_count"] == 2
    assert session["again_count"] == 1


def test_get_session_accuracy(db):
    session_id = db.start_session()
    db.update_session_stats(session_id, rating=5)
    db.update_session_stats(session_id, rating=5)
    db.update_session_stats(session_id, rating=0)
    db.update_session_stats(session_id, rating=0)

    session = db.get_session(session_id)
    assert session["accuracy_pct"] == 50.0


def test_get_session_reviews(db_with_card):
    session_id = db_with_card.start_session(stage="hiragana")
    card_id = db_with_card.get_due_cards()[0]["card_id"]
    db_with_card.update_card(card_id, 4, 1, 1, 2.5, session_id=session_id)

    session = db_with_card.get_session(session_id)
    assert len(session["reviews"]) == 1
    assert session["reviews"][0]["rating"] == 4
    assert session["reviews"][0]["character"] == "あ"


def test_get_session_not_found(db):
    assert db.get_session(9999) is None


def test_get_sessions_empty(db):
    assert db.get_sessions() == []
