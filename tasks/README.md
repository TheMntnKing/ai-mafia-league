# Project Progress

Single source of truth for delivery status and next steps.

## Status

MVP complete through Phase 6. Phase 7 complete (coordination fixes, context simplification,
SGR schema cleanup, prompt abstraction, persona modularization).

Completed phases:
- Phase 1: Project foundation
- Phase 2: LLM provider layer
- Phase 3: Game state & event system
- Phase 4: Context builder
- Phase 5: Player agent
- Phase 6: Game loop
- Phase 7: Quality and observability

See `tasks/phase1.md` through `tasks/phase6.md` for detailed deliverables.

## Next Steps (Draft)

Phase 8 focus (see `tasks/phase8.md`) is complete.

Phase 9 focus (see `tasks/phase9.md`):
- Replay viewer app (React + Vite)
- Phase navigation + public vs omniscient modes

## Post-MVP Ideas (Recovered)

### Personas & Community
- Persona data model with SQLite persistence
- Expand roster to 10+ personas with diverse entertainment styles
- Basic stats (games played, wins) for viewer interest (not ranking)
- Community persona submission format and guidelines

### CLI & Polish
- Rich console output during game
- Configuration file support
- Game replay viewer (Phase 9 scope)
- Better error messages

### Future Considerations
- 3+ Mafia support: redesign coordination (round-robin proposals or Mafia voting)
- Dynamic role counts (Doctor, Jester, etc.) would need new action types and phase hooks
- Additional providers (Gemini, OpenAI-compatible)
- Narrator system
- Tournament mode
- Evaluation framework
