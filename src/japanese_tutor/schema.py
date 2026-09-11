from typing import Literal

from pydantic import BaseModel, Field


class VocabularyCard(BaseModel):
    kanji: str = Field(..., description="The word in Kanji/Kana.")
    furigana: str | None = Field(None, description="Furigana for the Kanji.")
    english: str = Field(..., description="English translation.")
    notes: str | None = Field(None, description="Contextual notes or usage examples.")

class KanjiCard(BaseModel):
    character: str = Field(..., description="The Kanji character.")
    on_yomi: list[str] = Field(default_factory=list, description="On-yomi readings.")
    kun_yomi: list[str] = Field(default_factory=list, description="Kun-yomi readings.")
    meaning: str = Field(..., description="English meaning.")
    examples: list[str] = Field(default_factory=list, description="Example words using this Kanji.")

class GrammarCard(BaseModel):
    pattern: str = Field(..., description="The grammar pattern (e.g., ~は~です).")
    explanation: str = Field(..., description="Explanation of the grammar rule.")
    usage: str | None = Field(None, description="Usage rules or nuances.")
    examples: list[str] = Field(default_factory=list, description="Example sentences.")

class ReviewResult(BaseModel):
    suitability: Literal["pass", "fail", "warn"] = Field(..., description="Suitability of the image for extraction.")
    reason: str | None = Field(None, description="Reason for the suitability status.")
    post_type: Literal["vocabulary", "kanji", "grammar", "mixed"] = Field(..., description="Inferred content type.")
    word_count: int = Field(..., description="Approximate word count of extracted text.")
    summary: str = Field(..., description="2-3 sentence verdict on the extraction.")

class SessionStartRequest(BaseModel):
    stage: str | None = None
    provider: str | None = None
    model: str | None = None

class ReviewSubmission(BaseModel):
    card_id: int
    rating: int = Field(..., ge=0, le=5)
    session_id: int | None = None

class MnemonicRequest(BaseModel):
    character: str
    romaji: str

class MnemonicSaveRequest(BaseModel):
    card_id: int
    body: str
    source: str = "manual"

class DebriefRequest(BaseModel):
    missed: list[str]
    recurring: list[str] = []
