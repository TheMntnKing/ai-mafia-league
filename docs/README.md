# AI Mafia Agent League

AI agents playing competitive Mafia against each other. Entertainment-first content with strategic depth.

## What Is This

Seven AI agents play Mafia following competitive rules. Each agent has its own persona, maintains beliefs about other players, reasons about the game, and tries to win through deception and deduction.

Games produce watchable content where viewers see both public speech and private reasoning, creating dramatic irony.

## Status

**Current: Pre-development**

Documentation phase. Core docs complete, implementation not started.

## Documentation

- [01_vision.md](01_vision.md) - Why this exists, success criteria
- [02_game_rules.md](02_game_rules.md) - Competitive Mafia rules
- [03_system_design.md](03_system_design.md) - Components and game loop
- [04_player_agent.md](04_player_agent.md) - How players reason and act
- [05_context_management.md](05_context_management.md) - Information flow and formats
- [06_tech_stack.md](06_tech_stack.md) - Technical choices and rationale
- [07_implementation_plan.md](07_implementation_plan.md) - Phased build plan
- [08_future_features.md](08_future_features.md) - Post-MVP features
- [architecture.md](architecture.md) - Visual component diagrams (Mermaid)
- [schemas.py](schemas.py) - Pydantic schema definitions
- [database.sql](database.sql) - SQLite schema

## Tech Stack

See [06_tech_stack.md](06_tech_stack.md) for detailed technical choices.

**Summary:**
- **Language:** Python 3.11+
- **LLM Providers:** Claude Haiku 4.5 (primary), Gemini Flash 3.0, Qwen 3
- **Reasoning:** Schema-Guided Reasoning (SGR) for structured thinking
- **Storage:** SQLite (structured data) + JSON files (game logs)
- **Cost:** ~$0.20-0.80 per game (50-80 LLM calls)

## Running a Game

Not yet implemented.

Target usage:
```bash
python run_game.py --personas 7 --provider anthropic --output logs/game_001.json
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

See [08_future_features.md](08_future_features.md) for post-MVP features:
- Tournament format with persistent memory
- Post-game trash talk
- Additional roles (Don, Doctor)
- Competition platform
- Live streaming
- Visual game client
- Narrator system
- Evaluation framework
