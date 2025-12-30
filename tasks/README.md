# Project Progress

Single source of truth for delivery status and next steps.

## Status

MVP complete through Phase 6.

Completed phases:
- Phase 1: Project foundation
- Phase 2: LLM provider layer
- Phase 3: Game state & event system
- Phase 4: Context builder
- Phase 5: Player agent
- Phase 6: Game loop

See `tasks/phase1.md` through `tasks/phase6.md` for detailed deliverables.

## Next Steps (Draft)

Phase 7 focus (see `tasks/phase7.md`):
- Fix Mafia night coordination (sequential Round 1 proposals)
- Improve Day 1 nomination behavior via prompts
- Abstract prompts for easier tuning
- Improve log visibility and replay UX
- Expand test coverage with multi-run smoke tests

## Post-MVP Ideas (Recovered)

Personas & Community
- Persona data model with SQLite persistence
- Expand roster to 10+ personas with diverse entertainment styles
- Basic stats (games played, wins) for viewer interest (not ranking)
- Community persona submission format and guidelines

CLI & Polish
- Rich console output during game
- Configuration file support
- Game replay viewer
- Better error messages

Future
- Additional providers (Gemini, OpenAI-compatible)
- Narrator system
- Tournament mode
- Evaluation framework
