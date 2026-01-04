# AI Mafia Agent League

AI agents playing competitive Mafia against each other. Entertainment-first content with strategic depth.

## What Is This

Seven AI agents play Mafia following competitive rules. Each agent has its own persona, maintains beliefs about other players, reasons about the game, and tries to win through deception and deduction.

Games produce watchable content where viewers see both public speech and private reasoning, creating dramatic irony.

## Status

**Current: Game engine complete through Phase 8; Phase 9 archived; Phase 10 in progress**

Core game loop, providers, and tests are implemented.

## Documentation

- [01_vision.md](01_vision.md) - Why this exists, success criteria
- [02_game_rules.md](02_game_rules.md) - Competitive Mafia rules
- [engine_foundations.md](engine_foundations.md) - Engine architecture and invariants (Phases 1-7)
- [03_system_design.md](03_system_design.md) - Components and game loop
- [04_player_agent.md](04_player_agent.md) - How players reason and act
- [05_context_management.md](05_context_management.md) - Information flow and formats
- [06_tech_stack.md](06_tech_stack.md) - Technical choices and rationale
 
Progress tracking lives in `tasks/README.md`.
Roadmap lives in `tasks/roadmap.md`.

## Tech Stack

See [06_tech_stack.md](06_tech_stack.md) for detailed technical choices.

**Summary:**
- **Language:** Python 3.11+
- **LLM Providers:** Claude Haiku (primary, version configurable), Gemini Flash 3.0, Qwen 3
- **Reasoning:** Schema-Guided Reasoning (SGR) for structured thinking
- **Storage:** JSON files (game logs)
- **Cost:** ~$0.20-0.80 per game (50-80 LLM calls)

## Running a Game

Usage:
```bash
python -m src.engine.run --seed 123 --output logs/game_001.json --model claude-haiku-4-5-20251001
```

## Decisions Made

**Mafia coordination:** Up to 2 rounds of discussion. Prompts encourage round 1 agreement. If no consensus after 2 rounds, first Mafia (by seat order) decides. May agree to skip.

**Detective repeat investigation:** Allowed but discouraged. Wastes investigative power.

**Personas:** Bank of personas available each game. Not fixed per game. Tournaments (later) will have fixed personas with cumulative memory.

**Context compression:** Fixed 2 rounds of full detail. Older rounds always compressed to key facts.

**Observability:** Langfuse for LLM tracing, cost tracking, and debugging. See [06_tech_stack.md](06_tech_stack.md) for details.

## To Be Discussed

**Narrator implementation:** TBD based on streaming approach. Options: human narration, AI voice clone, or LLM-generated text. Depends on platform (YouTube/Twitch) and engagement testing.

**Testing strategy:** Need framework for collecting manual evaluation sets from game simulations. Component-level evals based on game history.

**Evaluation metrics:** Beyond win rate - what makes a game "good"? Entertainment value metrics need more thought. Possible factors: dramatic tension, close votes, surprise reveals, deception success rate.

## Future Features

See `tasks/roadmap.md` for post-MVP features.
