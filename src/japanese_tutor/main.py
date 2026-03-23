from pathlib import Path
from typing import List, Optional

import typer
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from local_first_common.cli import resolve_provider
from local_first_common.providers import PROVIDERS

from .characters import HIRAGANA, KATAKANA
from .db import Database
from .llm import LLMHelper
from .srs import SM2

app = FastAPI(title="Japanese Tutor")
cli = typer.Typer()
db: Optional[Database] = None
llm_helper: Optional[LLMHelper] = None

# API Models
class ReviewSubmission(BaseModel):
    card_id: int
    rating: int # 0-5

class MnemonicRequest(BaseModel):
    character: str
    romaji: str

# API Routes
@app.get("/api/cards/due")
def get_due_cards(stage: Optional[str] = None):
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db.get_due_cards(stage=stage)

@app.post("/api/reviews")
def submit_review(review: ReviewSubmission):
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    with db._get_connection() as conn:
        cursor = conn.execute("SELECT * FROM cards WHERE id = ?", (review.card_id,))
        card_row = cursor.fetchone()
        if not card_row:
            raise HTTPException(status_code=404, detail="Card not found")
        
        card = dict(card_row)
        
    next_interval, next_repetitions, next_ef = SM2.calculate_next_review(
        rating=review.rating,
        repetitions=card["repetitions"],
        interval=card["interval_days"],
        easiness_factor=card["easiness_factor"]
    )
    
    db.update_card(
        card_id=review.card_id,
        rating=review.rating,
        next_interval=next_interval,
        next_repetitions=next_repetitions,
        next_ef=next_ef
    )
    return {"status": "ok"}

@app.get("/api/mastery")
def get_mastery(stage: Optional[str] = None):
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db.get_mastery_stats(stage=stage)

@app.get("/api/example/{character}")
def get_example(character: str):
    if not db or not llm_helper:
        raise HTTPException(status_code=503, detail="Service unavailable")
    mastered = db.get_mastered_vocabulary()
    example = llm_helper.generate_adaptive_example(character, mastered)
    return {"example": example}

@app.post("/api/session/debrief")
def post_debrief(missed: List[str], recurring: List[str]):
    if not llm_helper:
        raise HTTPException(status_code=503, detail="LLM unavailable")
    debrief = llm_helper.generate_session_debrief(missed, recurring)
    return {"debrief": debrief}

@app.post("/api/mnemonics/generate")
def generate_mnemonics(req: MnemonicRequest):
    if not llm_helper:
        raise HTTPException(status_code=503, detail="LLM provider not available")
    suggestions = llm_helper.generate_mnemonics(req.character, req.romaji)
    return {"suggestions": suggestions}

@cli.command()
def serve(
    port: int = 8421,
    db_path: Optional[Path] = None,
    provider: str = "ollama",
    model: Optional[str] = None,
):
    """Start the Japanese Tutor SRS server."""
    global db, llm_helper
    db = Database(db_path)
    db.populate_characters(HIRAGANA + KATAKANA)
    
    try:
        llm_provider = resolve_provider(PROVIDERS, provider, model=model)
        llm_helper = LLMHelper(llm_provider)
    except Exception as e:
        print(f"Warning: Could not initialize LLM provider: {e}")

    # Static Files (UI)
    # Search for static folder relative to this file
    pkg_root = Path(__file__).parent.parent.parent
    static_path = pkg_root / "static"
    if static_path.exists():
        app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
    else:
        print(f"Warning: Static files not found at {static_path}")

    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    cli()
