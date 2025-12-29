#!/usr/bin/env python
"""Manual smoke test for AnthropicProvider (live API call)."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from collections.abc import Iterable

from src.providers import AnthropicProvider
from src.schemas import ActionType

try:
    from langfuse import Langfuse

    LANGFUSE_AVAILABLE = True
except ImportError:
    Langfuse = None  # type: ignore[assignment]
    LANGFUSE_AVAILABLE = False


def _parse_actions(value: str) -> list[ActionType]:
    if value.strip().lower() == "all":
        return list(ActionType)

    actions: list[ActionType] = []
    lookup = {a.value: a for a in ActionType}
    lookup.update({a.name.lower(): a for a in ActionType})

    for item in value.split(","):
        key = item.strip().lower()
        if not key:
            continue
        if key not in lookup:
            raise ValueError(f"Unknown action: {item}")
        actions.append(lookup[key])

    if not actions:
        raise ValueError("No actions provided")
    return actions


def _build_contexts() -> dict[ActionType, str]:
    base = (
        "Use the tool and fill every required field. Use empty lists or dicts "
        "when appropriate. Keep strings short and concrete. Do not invent facts "
        "or events beyond what is explicitly stated."
    )
    return {
        ActionType.SPEAK: (
            f"{base}\n"
            "You are Player 1 (Town). Phase: Day 1.\n"
            "Living players: Alice, Bob, Charlie.\n"
            "Task: Speak in 2-3 sentences and nominate one player."
        ),
        ActionType.VOTE: (
            f"{base}\n"
            "You are Player 1 (Town). Phase: Day 1 Voting.\n"
            "Nominated players: Alice, Bob.\n"
            "Task: Vote for one nominated player or skip."
        ),
        ActionType.NIGHT_KILL: (
            f"{base}\n"
            "You are Player 2 (Mafia). Your partner is Bob.\n"
            "Living players: Alice, Bob, Charlie. You may not target your partner.\n"
            "Task: Choose a kill target or skip."
        ),
        ActionType.INVESTIGATION: (
            f"{base}\n"
            "You are Player 3 (Detective).\n"
            "Living players: Alice, Bob, Charlie.\n"
            "Task: Choose a target to investigate (not yourself)."
        ),
        ActionType.LAST_WORDS: (
            f"{base}\n"
            "You are Player 4. You were eliminated.\n"
            "Task: Provide last words in one short paragraph."
        ),
        ActionType.DEFENSE: (
            f"{base}\n"
            "You are Player 5. You are tied for elimination.\n"
            "Task: Provide a brief defense statement."
        ),
    }


async def _run(actions: Iterable[ActionType], model: str, max_tokens: int) -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    langfuse_client = Langfuse() if LANGFUSE_AVAILABLE else None
    provider = AnthropicProvider(api_key=api_key, model=model, max_tokens=max_tokens)
    contexts = _build_contexts()

    for action in actions:
        context = contexts[action]
        print(f"\n=== {action.value} ===")
        result = await provider.act(action, context)
        print(result)

    if langfuse_client:
        langfuse_client.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description="AnthropicProvider smoke test.")
    parser.add_argument(
        "--actions",
        default="all",
        help="Comma-separated list (e.g., speak,vote) or 'all' (default).",
    )
    parser.add_argument(
        "--model",
        default="claude-haiku-4-5-20251001",
        help="Anthropic model name.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Max tokens for each response.",
    )
    args = parser.parse_args()

    try:
        actions = _parse_actions(args.actions)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    try:
        asyncio.run(_run(actions, args.model, args.max_tokens))
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
