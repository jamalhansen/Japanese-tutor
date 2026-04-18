from pathlib import Path
import os
from typing import Annotated, Optional

import typer

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
    init_config_option,
)
from local_first_common.config import get_setting
from local_first_common.tracking import register_tool

from . import api
from .characters import HIRAGANA, KATAKANA
from .db import Database
from .llm import LLMHelper

TOOL_NAME = "japanese-tutor"
DEFAULTS = {
    "provider": "ollama",
    "model": "llama3",
    "port": 8421,
}
_TOOL = register_tool(TOOL_NAME)

app = typer.Typer(help="Japanese Tutor SRS application.")

@app.command()
def run(
    port: Optional[int] = typer.Option(None, help="Server port"),
    db_path: Optional[Path] = typer.Option(None, help="Custom SQLite DB path"),
    provider: Annotated[str, provider_option()] = os.environ.get("MODEL_PROVIDER", "ollama"),
    model: Annotated[Optional[str], model_option()] = None,
    dry_run: Annotated[bool, dry_run_option()] = False,
    no_llm: Annotated[bool, no_llm_option()] = False,
    verbose: Annotated[bool, verbose_option()] = False,
    debug: Annotated[bool, debug_option()] = False,
    init_config: Annotated[bool, init_config_option(TOOL_NAME, DEFAULTS)] = False,
):
    """Start the Japanese Tutor SRS server."""
    
    # 1. Resolve configuration with standard precedence
    actual_port = get_setting(TOOL_NAME, "port", cli_val=port, default=8421)
    actual_provider = get_setting(TOOL_NAME, "provider", cli_val=provider, default="ollama")
    actual_model = get_setting(TOOL_NAME, "model", cli_val=model)
    actual_dry_run = resolve_dry_run(dry_run, no_llm)
    
    # 2. Initialize database
    api.db = Database(db_path)
    api.db.populate_characters(HIRAGANA + KATAKANA)
    
    # 3. Initialize LLM helper
    try:
        llm = resolve_provider(PROVIDERS, actual_provider, actual_model, debug=debug, no_llm=no_llm)
        api.llm = LLMHelper(llm, actual_dry_run)
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        if not no_llm:
            raise typer.Exit(1)

    # 4. Start server
    static_dir = Path(__file__).parent.parent.parent / "static"
    print(f"Starting Japanese Tutor at http://localhost:{actual_port}")
    api.start_server(actual_port, static_dir)

if __name__ == "__main__":
    app()
