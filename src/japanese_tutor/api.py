from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .db import Database
from .llm import LLMHelper
from .srs import SM2
from .schema import (
    ReviewSubmission,
    MnemonicRequest,
    DebriefRequest,
    MnemonicSaveRequest,
    SessionStartRequest,
)


class TutorDBError(Exception):
    """Raised when a tutor database operation fails."""


app = FastAPI(title="Japanese Tutor")

# Global state to be initialized by CLI
db: Optional[Database] = None
llm_helper: Optional[LLMHelper] = None


@app.get("/api/cards/due")
def get_due_cards(stage: Optional[str] = None, practice: bool = False):
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        if stage is None:
            if not db.is_stage_mastered("hiragana"):
                stage = "hiragana"
            elif not db.is_stage_mastered("katakana"):
                stage = "katakana"
            else:
                stage = "kanji"
        return db.get_due_cards(stage=stage, practice=practice)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.post("/api/reviews")
def submit_review(review: ReviewSubmission):
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        card = db.get_card(review.card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")

        next_interval, next_repetitions, next_ef = SM2.calculate_next_review(
            rating=review.rating,
            repetitions=card["repetitions"],
            interval=card["interval_days"],
            easiness_factor=card["easiness_factor"],
        )

        db.update_card(
            card_id=review.card_id,
            rating=review.rating,
            next_interval=next_interval,
            next_repetitions=next_repetitions,
            next_ef=next_ef,
            session_id=review.session_id,
        )

        if review.session_id:
            db.update_session_stats(review.session_id, review.rating)

        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


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


@app.post("/api/session/start")
def start_session(req: SessionStartRequest):
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        session_id = db.start_session(
            stage=req.stage, provider=req.provider, model=req.model
        )
        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.post("/api/session/end/{session_id}")
def end_session(session_id: int):
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        db.end_session(session_id)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/api/sessions")
def get_sessions(limit: int = 20):
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        return db.get_sessions(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/api/sessions/{session_id}")
def get_session(session_id: int):
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


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


@app.post("/api/mnemonics/save")
def save_mnemonic(req: MnemonicSaveRequest):
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")

    card = db.get_card(req.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.save_mnemonic(card["character_id"], req.body, req.source)
    return {"status": "ok"}


def mount_static(pkg_root: Path):
    static_path = pkg_root / "static"
    if static_path.exists():
        app.mount(
            "/", StaticFiles(directory=str(static_path), html=True), name="static"
        )
    else:
        # Fallback for development if static is one level up from src/japanese_tutor
        static_path = pkg_root.parent / "static"
        if static_path.exists():
            app.mount(
                "/", StaticFiles(directory=str(static_path), html=True), name="static"
            )


def start_server(port: int, pkg_root: Path):
    """Entry point for starting the FastAPI server."""
    import uvicorn

    mount_static(pkg_root)
    uvicorn.run(app, host="0.0.0.0", port=port)
