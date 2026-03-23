from pathlib import Path
from typing import Optional

import typer
import uvicorn

from local_first_common.providers import PROVIDERS
from local_first_common.cli import (
    provider_option,
    model_option,
    dry_run_option,
    no_llm_option,
    verbose_option,
    debug_option,
    resolve_provider,
    resolve_dry_run,
)
from local_first_common.tracking import register_tool

from . import api
from .characters import HIRAGANA, KATAKANA
from .db import Database
from .llm import LLMHelper

_TOOL = register_tool("japanese-tutor")

app = typer.Typer(help="Japanese Tutor SRS application.")

@app.command()
def run(
    port: int = typer.Option(8421, help="Server port"),
    db_path: Optional[Path] = typer.Option(None, help="Custom SQLite DB path"),
    provider: str = provider_option(),
    model: Optional[str] = model_option(),
    dry_run: bool = dry_run_option(),
    no_llm: bool = no_llm_option(),
    verbose: bool = verbose_option(),
    debug: bool = debug_option(),
):
    """Start the Japanese Tutor SRS server."""
    
    # 1. Resolve configuration
    actual_dry_run = resolve_dry_run(dry_run, no_llm)
    
    # 2. Initialize database
    api.db = Database(db_path)
    api.db.populate_characters(HIRAGANA + KATAKANA)
    
    # 3. Initialize LLM helper
    try:
        llm_provider = resolve_provider(
            PROVIDERS, 
            provider, 
            model=model, 
            debug=debug, 
            verbose=verbose, 
            no_llm=no_llm
        )
        api.llm_helper = LLMHelper(llm_provider)
    except Exception as e:
        if verbose or debug:
            typer.secho(f"Warning: Could not initialize LLM provider: {e}", fg=typer.colors.YELLOW)

    # 4. Setup FastAPI and mount static files
    pkg_root = Path(__file__).parent.parent.parent
    api.mount_static(pkg_root)
    
    if actual_dry_run:
        typer.secho(f"[dry-run] Server starting at http://localhost:{port}", fg=typer.colors.CYAN)
    
    typer.echo(f"Starting server at http://localhost:{port}")
    uvicorn.run(api.app, host="0.0.0.0", port=port)

def main_entry():
    app()

if __name__ == "__main__":
    main_entry()
