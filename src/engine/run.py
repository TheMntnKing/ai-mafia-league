"""CLI entry point for running Mafia games."""

from __future__ import annotations

import argparse
import asyncio
import sys

from rich.console import Console
from rich.panel import Panel

from src.config import get_settings
from src.engine.game import GameConfig, GameRunner
from src.providers.anthropic import AnthropicProvider
from src.schemas import Event

console = Console()


def _cli_event_reporter(console: Console):
    """Build a lightweight CLI reporter for key game events."""
    def _report(event: Event) -> None:
        if event.type == "phase_start":
            phase = event.data.get("phase", "unknown")
            console.print(f"[bold]Phase:[/bold] {phase}")
        elif event.type == "night_resolution":
            target = event.data.get("actual_kill") or "none"
            console.print(f"Night kill: {target}")
        elif event.type == "vote_round":
            outcome = event.data.get("outcome", "unknown")
            round_number = event.data.get("round")
            label = f"Vote round {round_number}" if round_number else "Vote"
            console.print(f"{label}: {outcome}")
        elif event.type == "elimination":
            eliminated = event.data.get("eliminated", "unknown")
            console.print(f"Eliminated: {eliminated}")
        elif event.type == "game_end":
            winner = event.data.get("winner", "unknown")
            console.print(f"[bold]Game end:[/bold] {winner}")

    return _report


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run an AI Mafia game",
        prog="python -m src.engine.run",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for game logs (default: from settings)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to use (default: from settings)",
    )
    return parser.parse_args()


async def run_game_cli(args: argparse.Namespace) -> int:
    """Run a game from CLI arguments."""
    settings = get_settings()

    # Check for API key
    if not settings.anthropic_api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not set[/red]")
        console.print("Set it in your environment or .env file")
        return 1

    # Load personas
    try:
        from src.personas.initial import get_personas
        personas = get_personas()
    except ImportError:
        console.print("[red]Error: No personas defined[/red]")
        console.print("Create personas in src/personas/initial.py")
        return 1

    if len(personas) != 10:
        console.print(f"[red]Error: Expected 10 personas, got {len(personas)}[/red]")
        return 1

    # Create provider
    model = args.model or settings.model_name
    provider = AnthropicProvider(
        api_key=settings.anthropic_api_key,
        model=model,
    )

    # Create game config
    output_dir = args.output or settings.logs_dir
    config = GameConfig(
        player_names=list(personas.keys()),
        personas=personas,
        provider=provider,
        output_dir=output_dir,
        seed=args.seed,
    )

    # Display game start
    console.print(Panel.fit(
        f"[bold]AI Mafia Game[/bold]\n"
        f"Players: {', '.join(config.player_names)}\n"
        f"Model: {model}\n"
        f"Seed: {args.seed or 'random'}",
        title="Game Starting",
    ))

    # Run game
    runner = GameRunner(config)
    runner.event_log.add_observer(_cli_event_reporter(console))

    try:
        result = await runner.run()
    except Exception as e:
        console.print(f"[red]Game failed: {e}[/red]")
        raise

    # Display result
    winner_color = "green" if result.winner == "town" else "red"
    console.print(Panel.fit(
        f"[bold {winner_color}]Winner: {result.winner.upper()}[/bold {winner_color}]\n"
        f"Rounds: {result.rounds}\n"
        f"Survivors: {', '.join(result.final_living)}\n"
        f"Log: {result.log_path}",
        title="Game Complete",
    ))

    return 0


def main() -> int:
    """Main entry point."""
    args = parse_args()
    return asyncio.run(run_game_cli(args))


if __name__ == "__main__":
    sys.exit(main())
