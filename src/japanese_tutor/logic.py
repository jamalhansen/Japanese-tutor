from pathlib import Path
from typing import Annotated, Optional

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
    init_config_option,
)
from local_first_common.tracking import register_tool
from local_first_common.config import get_setting

from . import api
from .characters import HIRAGANA, KATAKANA
from .db import Database
from .llm import LLMHelper

TOOL_NAME = "japanese-tutor"
_TOOL = register_tool(TOOL_NAME)

app = typer.Typer(help="Japanese Tutor SRS application.")

DEFAULTS = {
    "provider": "ollama",
    "model": "llama3",
    "port": 8421,
}

@app.command()
def run(
    port: Annotated[Optional[int], typer.Option(help="Server port")] = None,
    db_path: Annotated[Optional[Path], typer.Option(help="Custom SQLite DB path")] = None,
    provider: Annotated[Optional[str], provider_option()] = None,
    model: Annotated[Optional[str], model_option()] = None,
    dry_run: bool = dry_run_option(),
    no_llm: bool = no_llm_option(),
    verbose: bool = verbose_option(),
    debug: bool = debug_option(),
    init_config: bool = init_config_option(TOOL_NAME, DEFAULTS),
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
