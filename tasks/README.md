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

- Improve Mafia night coordination (consider sequential R1 proposals)
- Improve prompt tuning (speech length, nomination justification)
- Add log/replay viewer for easier game review
- Expand test coverage with multi-run smoke tests
- Optional: add private Night Zero strategy events to logs

## Post-MVP Phases (Recovered)

Phase 7: Personas & Community
- Persona data model with SQLite persistence
- Expand roster to 10+ personas with diverse entertainment styles
- Basic stats (games played, wins) for viewer interest (not ranking)
- Community persona submission format and guidelines

Phase 8: CLI & Polish
- Rich console output during game
- Configuration file support
- Game replay viewer
- Better error messages

Future
- Additional providers (Gemini, OpenAI-compatible)
- Narrator system
- Tournament mode
- Evaluation framework
