import csv
import io
from pathlib import Path

from .schema import GrammarCard, KanjiCard, VocabularyCard

Card = VocabularyCard | KanjiCard | GrammarCard


def _table(cards: list[Card]) -> tuple[list[str], list[list[str]]]:
    """Headers and rows for a non-empty list of one card type (the first card decides)."""
    first = cards[0]
    if isinstance(first, VocabularyCard):
        vocab = [c for c in cards if isinstance(c, VocabularyCard)]
        headers = ["Kanji", "Furigana", "English", "Notes"]
        rows = [[c.kanji, c.furigana or "", c.english, c.notes or ""] for c in vocab]
    elif isinstance(first, KanjiCard):
        kanji = [c for c in cards if isinstance(c, KanjiCard)]
        headers = ["Character", "On-yomi", "Kun-yomi", "Meaning", "Examples"]
        rows = [
            [c.character, ", ".join(c.on_yomi), ", ".join(c.kun_yomi), c.meaning, "; ".join(c.examples)] for c in kanji
        ]
    elif isinstance(first, GrammarCard):
        grammar = [c for c in cards if isinstance(c, GrammarCard)]
        headers = ["Pattern", "Explanation", "Usage", "Examples"]
        rows = [[c.pattern, c.explanation, c.usage or "", "; ".join(c.examples)] for c in grammar]
    else:
        raise TypeError(f"Unknown card type: {type(first)}")
    if len(rows) != len(cards):
        raise ValueError("Cards of different types can't share one CSV")
    return headers, rows


def export_to_csv(cards: list[Card], output_path: Path):
    """Export cards to a CSV format suitable for Anki import."""
    if not cards:
        return
    headers, rows = _table(cards)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def cards_to_string(cards: list[Card]) -> str:
    """Convert cards to a CSV string for previewing in dry-run."""
    if not cards:
        return "No cards generated."
    headers, rows = _table(cards)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue()
