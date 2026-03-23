import csv
import io
from pathlib import Path
from typing import List, Union
from .schema import GrammarCard, KanjiCard, VocabularyCard

def export_to_csv(cards: List[Union[VocabularyCard, KanjiCard, GrammarCard]], output_path: Path):
    """Export cards to a CSV format suitable for Anki import."""
    if not cards:
        return

    # Determine headers based on card type
    card_type = type(cards[0])
    
    if card_type == VocabularyCard:
        headers = ["Kanji", "Furigana", "English", "Notes"]
        rows = [[c.kanji, c.furigana or "", c.english, c.notes or ""] for c in cards] # type: ignore
    elif card_type == KanjiCard:
        headers = ["Character", "On-yomi", "Kun-yomi", "Meaning", "Examples"]
        rows = [
            [
                c.character, 
                ", ".join(c.on_yomi), 
                ", ".join(c.kun_yomi), 
                c.meaning, 
                "; ".join(c.examples)
            ] for c in cards # type: ignore
        ]
    elif card_type == GrammarCard:
        headers = ["Pattern", "Explanation", "Usage", "Examples"]
        rows = [
            [
                c.pattern, 
                c.explanation, 
                c.usage or "", 
                "; ".join(c.examples)
            ] for c in cards # type: ignore
        ]
    else:
        raise ValueError(f"Unknown card type: {card_type}")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

def cards_to_string(cards: List[Union[VocabularyCard, KanjiCard, GrammarCard]]) -> str:
    """Convert cards to a CSV string for previewing in dry-run."""
    if not cards:
        return "No cards generated."
        
    output = io.StringIO()
    # Logic similar to export_to_csv but writing to string
    card_type = type(cards[0])
    if card_type == VocabularyCard:
        headers = ["Kanji", "Furigana", "English", "Notes"]
        rows = [[c.kanji, c.furigana or "", c.english, c.notes or ""] for c in cards] # type: ignore
    elif card_type == KanjiCard:
        headers = ["Character", "On-yomi", "Kun-yomi", "Meaning", "Examples"]
        rows = [[c.character, ", ".join(c.on_yomi), ", ".join(c.kun_yomi), c.meaning, "; ".join(c.examples)] for c in cards] # type: ignore
    elif card_type == GrammarCard:
        headers = ["Pattern", "Explanation", "Usage", "Examples"]
        rows = [[c.pattern, c.explanation, c.usage or "", "; ".join(c.examples)] for c in cards] # type: ignore
    
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue()
