# Japanese Flashcard Generator (`japanese-tutor`)

Tool #8 in the `local-ai-tools` series. Automates the creation of Anki flashcards from Japanese textbook images using LLMWhisperer for OCR and Gemini/Anthropic for intelligent extraction.

## Critical rules

- **Use LLMWhisperer** for all OCR tasks. Do not use generic OCR.
- **Support 3 modes**: `vocab`, `kanji`, `grammar`.
- **Anki compatibility**: CSV output must be importable into Anki without manual reformatting.
- **Suitability Check**: Always perform a suitability check before processing an image to save OCR credits.

## Run Tracking
Every run must be tracked via `local-first-common.tracking.timed_run`.

## Development
```bash
uv sync
uv run pytest
```
