#!/usr/bin/env python3
"""Pretty-print a game log for quick human review."""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path


def _wrap_line(prefix: str, text: str, width: int) -> str:
    if not text:
        return prefix.rstrip()
    wrapper = textwrap.TextWrapper(
        width=width, initial_indent=prefix, subsequent_indent=" " * len(prefix)
    )
    return wrapper.fill(text)


def _parse_eliminated(outcome: str | None) -> str | None:
    if not outcome:
        return None
    if outcome.startswith("eliminated:"):
        return outcome.split(":", 1)[1]
    return None


def _format_players(players: list[dict]) -> None:
    print("Players:")
    for p in sorted(players, key=lambda x: x.get("seat", 0)):
        seat = p.get("seat", "?")
        name = p.get("name", "unknown")
        role = p.get("role", "unknown")
        outcome = p.get("outcome", "unknown")
        print(f"- Seat {seat}: {name} ({role}, {outcome})")


def _format_transcript(transcript: list[dict], last_words: dict[str, str], width: int) -> None:
    if not transcript:
        print("Transcript: <none>")
        return

    print("Transcript:")
    for round_t in transcript:
        round_number = round_t.get("round_number", "?")
        print(f"\nDay {round_number}")
        night_kill = round_t.get("night_kill")
        if night_kill:
            print(f"- Night kill: {night_kill}")
        else:
            print("- Night kill: none")

        speeches = round_t.get("speeches", [])
        if speeches:
            print("- Speeches:")
            for speech in speeches:
                speaker = speech.get("speaker", "unknown")
                text = speech.get("text", "")
                nomination = speech.get("nomination")
                print(_wrap_line(f"  - {speaker}: ", text, width))
                if nomination:
                    print(f"    Nomination: {nomination}")
        else:
            print("- Speeches: none")

        defense_speeches = round_t.get("defense_speeches") or []
        if defense_speeches:
            print("- Defense speeches:")
            for defense in defense_speeches:
                speaker = defense.get("speaker", "unknown")
                text = defense.get("text", "")
                print(_wrap_line(f"  - {speaker}: ", text, width))

        votes = round_t.get("votes") or {}
        if votes:
            print("- Votes:")
            for voter in sorted(votes.keys()):
                print(f"  - {voter} -> {votes[voter]}")
        else:
            print("- Votes: none")

        vote_outcome = round_t.get("vote_outcome")
        if vote_outcome:
            print(f"- Vote outcome: {vote_outcome}")

        revote = round_t.get("revote") or {}
        if revote:
            print("- Revote:")
            for voter in sorted(revote.keys()):
                print(f"  - {voter} -> {revote[voter]}")

        revote_outcome = round_t.get("revote_outcome")
        if revote_outcome:
            print(f"- Revote outcome: {revote_outcome}")

        eliminated = _parse_eliminated(revote_outcome) or _parse_eliminated(vote_outcome)
        if eliminated and eliminated in last_words:
            print(_wrap_line("- Last words: ", f"{eliminated}: {last_words[eliminated]}", width))


def _format_events(events: list[dict], public_only: bool, width: int) -> None:
    print("\nEvents:")
    for idx, event in enumerate(events, start=1):
        event_type = event.get("type", "unknown")
        data = event.get("data", {})
        private_fields = set(event.get("private_fields") or [])

        if public_only and private_fields:
            if private_fields.issuperset(data.keys()):
                continue
            data = {k: v for k, v in data.items() if k not in private_fields}

        serialized = json.dumps(data, ensure_ascii=True, indent=2)
        header = f"- {idx}. {event_type}"
        print(header)
        for line in serialized.splitlines():
            print(_wrap_line("  ", line, width))


def main() -> int:
    parser = argparse.ArgumentParser(description="Pretty-print a Mafia game log.")
    parser.add_argument("log_path", type=Path, help="Path to a game_*.json log file.")
    parser.add_argument("--show-events", action="store_true", help="Include raw event log.")
    parser.add_argument(
        "--public",
        action="store_true",
        help="Hide private fields when showing events.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=100,
        help="Wrap output to this width (default: 100).",
    )
    args = parser.parse_args()

    if not args.log_path.exists():
        print(f"Log not found: {args.log_path}")
        return 1

    with args.log_path.open() as f:
        log_data = json.load(f)

    print(f"Game: {log_data.get('game_id', 'unknown')}")
    print(f"Winner: {log_data.get('winner', 'unknown')}")
    print(f"Rounds: {log_data.get('result', {}).get('rounds', 'unknown')}")

    players = log_data.get("players", [])
    if players:
        _format_players(players)

    events = log_data.get("events", [])
    last_words = {
        e.get("data", {}).get("speaker", ""): e.get("data", {}).get("text", "")
        for e in events
        if e.get("type") == "last_words"
    }

    transcript = log_data.get("transcript", [])
    _format_transcript(transcript, last_words, args.width)

    if args.show_events and events:
        _format_events(events, args.public, args.width)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
