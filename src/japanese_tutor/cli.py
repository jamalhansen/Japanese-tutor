from pathlib import Path
from typing import Annotated, Literal, Optional

import typer
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
from rich.console import Console

from .anki import cards_to_string, export_to_csv
from .logic import TutorLogic

app = typer.Typer(help="Japanese Flashcard Generator from textbook images.")
console = Console()

def run_tutor(
    image: Path,
    mode: Literal["vocabulary", "kanji", "grammar"],
    provider_name: str,
    model: Optional[str],
    dry_run: bool,
    no_llm: bool,
    verbose: bool,
    debug: bool,
    custom_instructions: str = "",
    output: Optional[Path] = None,
):
    dry_run = resolve_dry_run(dry_run, no_llm)
    
    # Gemini is the recommended provider for vision/suitability
    llm = resolve_provider(PROVIDERS, provider_name, model, debug=debug, verbose=verbose, no_llm=no_llm)
    
    logic = TutorLogic(provider=llm)
    
    try:
        cards = logic.process_image(image, mode, custom_instructions)
        
        if not cards:
            console.print("[red]No cards were generated.[/red]")
            return

        csv_content = cards_to_string(cards)
        
        if dry_run:
            console.print(f"\n[cyan][dry-run] Generated {len(cards)} {mode} cards:[/cyan]")
            console.print(csv_content)
        else:
            out_file = output or Path(f"{image.stem}_{mode}.csv")
            export_to_csv(cards, out_file)
            console.print(f"[green]Successfully exported {len(cards)} cards to {out_file}[/green]")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if debug:
            raise e

@app.command()
def vocab(
    image: Annotated[Path, typer.Argument(help="Path to the textbook image")],
    provider: Annotated[str, provider_option(default="gemini")] = "gemini",
    model: Annotated[Optional[str], model_option()] = None,
    dry_run: Annotated[bool, dry_run_option()] = False,
    no_llm: Annotated[bool, no_llm_option()] = False,
    verbose: Annotated[bool, verbose_option()] = False,
    debug: Annotated[bool, debug_option()] = False,
    instructions: Annotated[str, typer.Option("--instructions", "-i", help="Custom extraction instructions")] = "",
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Custom output CSV path")] = None,
):
    """Generate Vocabulary cards."""
    run_tutor(image, "vocabulary", provider, model, dry_run, no_llm, verbose, debug, instructions, output)

@app.command()
def kanji(
    image: Annotated[Path, typer.Argument(help="Path to the textbook image")],
    provider: Annotated[str, provider_option(default="gemini")] = "gemini",
    model: Annotated[Optional[str], model_option()] = None,
    dry_run: Annotated[bool, dry_run_option()] = False,
    no_llm: Annotated[bool, no_llm_option()] = False,
    verbose: Annotated[bool, verbose_option()] = False,
    debug: Annotated[bool, debug_option()] = False,
    instructions: Annotated[str, typer.Option("--instructions", "-i", help="Custom extraction instructions")] = "",
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Custom output CSV path")] = None,
):
    """Generate Kanji cards."""
    run_tutor(image, "kanji", provider, model, dry_run, no_llm, verbose, debug, instructions, output)

@app.command()
def grammar(
    image: Annotated[Path, typer.Argument(help="Path to the textbook image")],
    provider: Annotated[str, provider_option(default="gemini")] = "gemini",
    model: Annotated[Optional[str], model_option()] = None,
    dry_run: Annotated[bool, dry_run_option()] = False,
    no_llm: Annotated[bool, no_llm_option()] = False,
    verbose: Annotated[bool, verbose_option()] = False,
    debug: Annotated[bool, debug_option()] = False,
    instructions: Annotated[str, typer.Option("--instructions", "-i", help="Custom extraction instructions")] = "",
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Custom output CSV path")] = None,
):
    """Generate Grammar cards."""
    run_tutor(image, "grammar", provider, model, dry_run, no_llm, verbose, debug, instructions, output)

if __name__ == "__main__":
    app()
