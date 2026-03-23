from pathlib import Path
from typing import Annotated, List, Optional

import typer
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from local_first_common.cli import (
    debug_option,
    dry_run_option,
    model_option,
    no_llm_option,
    provider_option,
    resolve_dry_run,
    resolve_provider,
    verbose_option,
)
from local_first_common.providers import PROVIDERS
from local_first_common.tracking import register_tool

from .characters import HIRAGANA, KATAKANA
from .db import Database
from .llm import LLMHelper
from .srs import SM2

_TOOL = register_tool("japanese-tutor")

app = FastAPI(title="Japanese Tutor")
cli = typer.Typer(help="Japanese Tutor SRS application.")
db: Optional[Database] = None
llm_helper: Optional[LLMHelper] = None

# API Models
class ReviewSubmission(BaseModel):
    card_id: int
    rating: int # 0-5

class MnemonicRequest(BaseModel):
    character: str
    romaji: str

class DebriefRequest(BaseModel):
    missed: List[str]
    recurring: List[str] = []

# API Routes
@app.get("/api/cards/due")
def get_due_cards(stage: Optional[str] = None):
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    if stage is None:
        # Determine current stage
        if not db.is_stage_mastered("hiragana"):
            stage = "hiragana"
        elif not db.is_stage_mastered("katakana"):
            stage = "katakana"
        else:
            stage = "kanji"
            
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
def post_debrief(req: DebriefRequest):
    if not llm_helper:
        raise HTTPException(status_code=503, detail="LLM unavailable")
    debrief = llm_helper.generate_session_debrief(req.missed, req.recurring)
    return {"debrief": debrief}

@app.post("/api/mnemonics/generate")
def generate_mnemonics(req: MnemonicRequest):
    if not llm_helper:
        raise HTTPException(status_code=503, detail="LLM provider not available")
    suggestions = llm_helper.generate_mnemonics(req.character, req.romaji)
    return {"suggestions": suggestions}

@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    port: Annotated[int, typer.Option(help="Server port")] = 8421,
    db_path: Annotated[Optional[Path], typer.Option(help="Custom SQLite DB path")] = None,
    provider_name: Annotated[str, provider_option(default="ollama")] = "ollama",
    model: Annotated[Optional[str], model_option()] = None,
    importer_model: Annotated[Optional[str], typer.Option(help="Model for OCR/Vision tasks (e.g. @vision)")] = None,
    dry_run: Annotated[bool, dry_run_option()] = False,
    no_llm: Annotated[bool, no_llm_option()] = False,
    verbose: Annotated[bool, verbose_option()] = False,
    debug: Annotated[bool, debug_option()] = False,
):
    """Start the Japanese Tutor SRS server."""
    if ctx.invoked_subcommand is not None:
        return
        
    global db, llm_helper
    
    # Standard rule: --no-llm always implies --dry-run
    dry_run = resolve_dry_run(dry_run, no_llm)
    
    db = Database(db_path)
    db.populate_characters(HIRAGANA + KATAKANA)
    
    try:
        llm_provider = resolve_provider(
            PROVIDERS, 
            provider_name, 
            model=model, 
            debug=debug, 
            verbose=verbose, 
            no_llm=no_llm
        )
        llm_helper = LLMHelper(llm_provider)
    except Exception as e:
        if verbose or debug:
            print(f"Warning: Could not initialize LLM provider: {e}")

    # Static Files (UI)
    pkg_root = Path(__file__).parent.parent.parent
    static_path = pkg_root / "static"
    if static_path.exists():
        app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
    
    print(f"Starting server at http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

def main_entry():
    cli()

if __name__ == "__main__":
    cli()
