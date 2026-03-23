import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

class Database:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            sync_dir = Path.home() / "sync" / "japanese-tutor"
            sync_dir.mkdir(parents=True, exist_ok=True)
            db_path = sync_dir / "japanese_tutor.db"
            
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY,
                    stage TEXT NOT NULL,
                    character TEXT NOT NULL UNIQUE,
                    romaji TEXT NOT NULL,
                    meaning TEXT,
                    stroke_order_notes TEXT,
                    jlpt_level INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY,
                    character_id INTEGER NOT NULL,
                    easiness_factor REAL DEFAULT 2.5,
                    interval_days INTEGER DEFAULT 0,
                    repetitions INTEGER DEFAULT 0,
                    next_review_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_reviewed_at TIMESTAMP,
                    consecutive_correct INTEGER DEFAULT 0,
                    romaji_visible BOOLEAN DEFAULT 1,
                    FOREIGN KEY (character_id) REFERENCES characters(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY,
                    card_id INTEGER NOT NULL,
                    session_id INTEGER,
                    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    rating INTEGER NOT NULL,
                    response_time_ms INTEGER,
                    romaji_visible BOOLEAN,
                    stage TEXT,
                    FOREIGN KEY (card_id) REFERENCES cards(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS associations (
                    id INTEGER PRIMARY KEY,
                    character_id INTEGER NOT NULL,
                    body TEXT NOT NULL,
                    source TEXT,
                    chosen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    internalized_at TIMESTAMP,
                    resurface_count INTEGER DEFAULT 0,
                    FOREIGN KEY (character_id) REFERENCES characters(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    stage TEXT,
                    cards_reviewed INTEGER DEFAULT 0,
                    correct_count INTEGER DEFAULT 0,
                    again_count INTEGER DEFAULT 0,
                    provider TEXT,
                    model TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_runs (
                    id INTEGER PRIMARY KEY,
                    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    provider TEXT,
                    model TEXT,
                    cards_reviewed INTEGER,
                    duration_ms INTEGER,
                    error TEXT
                )
            """)

    def populate_characters(self, characters_list: List[Dict[str, Any]]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM characters")
            if cursor.fetchone()[0] == 0:
                for char in characters_list:
                    conn.execute(
                        "INSERT INTO characters (stage, character, romaji, meaning) VALUES (?, ?, ?, ?)",
                        (char["stage"], char["char"], char["romaji"], char.get("meaning"))
                    )
                conn.execute("""
                    INSERT INTO cards (character_id)
                    SELECT id FROM characters
                """)

    def get_due_cards(self, stage: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            query = """
                SELECT c.id as card_id, ch.character, ch.romaji, ch.meaning, ch.stage,
                       c.easiness_factor, c.interval_days, c.repetitions, c.next_review_at,
                       c.romaji_visible,
                       a.body as mnemonic
                FROM cards c
                JOIN characters ch ON c.character_id = ch.id
                LEFT JOIN associations a ON a.character_id = ch.id
                WHERE c.next_review_at <= CURRENT_TIMESTAMP
            """
            params = []
            if stage:
                query += " AND ch.stage = ?"
                params.append(stage)
            
            query += " ORDER BY c.next_review_at LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_card(self, card_id: int, rating: int, next_interval: int, next_repetitions: int, next_ef: float):
        now = datetime.now()
        next_review = now + timedelta(days=next_interval)
        
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT consecutive_correct, romaji_visible FROM cards WHERE id = ?", (card_id,))
            current = cursor.fetchone()
            consecutive = current["consecutive_correct"]
            visible = current["romaji_visible"]
            
            if rating >= 3:
                consecutive += 1
                if consecutive >= 5:
                    visible = 0
            else:
                consecutive = 0
                visible = 1
                
            conn.execute("""
                UPDATE cards
                SET easiness_factor = ?,
                    interval_days = ?,
                    repetitions = ?,
                    next_review_at = ?,
                    last_reviewed_at = ?,
                    consecutive_correct = ?,
                    romaji_visible = ?
                WHERE id = ?
            """, (next_ef, next_interval, next_repetitions, next_review, now, consecutive, visible, card_id))
            
            conn.execute("""
                INSERT INTO reviews (card_id, rating, reviewed_at)
                VALUES (?, ?, ?)
            """, (card_id, rating, now))

    def get_mastery_stats(self, stage: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            query = """
                SELECT ch.character, ch.romaji, ch.stage,
                       c.easiness_factor, c.interval_days, c.repetitions,
                       c.consecutive_correct, c.romaji_visible,
                       (SELECT ROUND(AVG(CASE WHEN r.rating >= 3 THEN 1.0 ELSE 0.0 END) * 100, 1)
                        FROM reviews r WHERE r.card_id = c.id) as accuracy
                FROM characters ch
                JOIN cards c ON ch.id = c.character_id
            """
            params = []
            if stage:
                query += " WHERE ch.stage = ?"
                params.append(stage)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_mastered_vocabulary(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT ch.character FROM characters ch
                JOIN cards c ON ch.id = c.character_id
                WHERE c.consecutive_correct >= 5 OR c.interval_days > 14
            """)
            return [row["character"] for row in cursor.fetchall()]

    def is_stage_mastered(self, stage: str, threshold: float = 90.0) -> bool:
        """Check if 90% accuracy reached for all characters in a stage with no reviews due."""
        with self._get_connection() as conn:
            # Check if any cards in this stage are still due
            cursor = conn.execute("""
                SELECT COUNT(*) FROM cards c
                JOIN characters ch ON c.character_id = ch.id
                WHERE ch.stage = ? AND c.next_review_at <= CURRENT_TIMESTAMP
            """, (stage,))
            if cursor.fetchone()[0] > 0:
                return False

            # Check average accuracy of last 20 reviews for each character in stage
            # For simplicity, we'll check if the overall accuracy for characters in this stage is high enough
            cursor = conn.execute("""
                SELECT AVG(accuracy) FROM (
                    SELECT (SELECT ROUND(AVG(CASE WHEN r.rating >= 3 THEN 1.0 ELSE 0.0 END) * 100, 1)
                            FROM (SELECT rating FROM reviews WHERE card_id = c.id ORDER BY reviewed_at DESC LIMIT 20) r) as accuracy
                    FROM cards c
                    JOIN characters ch ON c.character_id = ch.id
                    WHERE ch.stage = ?
                )
            """, (stage,))
            avg_accuracy = cursor.fetchone()[0]
            return avg_accuracy is not None and avg_accuracy >= threshold

    def get_card(self, card_id: int) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT c.*, ch.character, ch.romaji, ch.stage
                FROM cards c
                JOIN characters ch ON c.character_id = ch.id
                WHERE c.id = ?
            """, (card_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}
