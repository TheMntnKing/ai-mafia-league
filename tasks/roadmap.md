# Roadmap

Forward-looking plan. Current delivery status lives in `tasks/README.md`.

## Near Term (Phases 9-11)

### Phase 9: 10-Player Expansion + Night Event Decomposition
- Move engine to 10 players (3 Mafia + Doctor + Detective + 5 Town).
- Support multi-partner Mafia coordination (majority rules, tie-break by lowest seat).
- Decompose night log into `mafia_discussion`, `mafia_vote`, `doctor_protection`,
  `investigation`, `night_resolution`.
- Update prompts/context for multi-partner Mafia and Doctor actions.
- Align viewer parser with new event stream.

### Phase 10: 3D Replay Viewer (Stylized Mesh)
- Finish character roster and scene GLBs (town square, mafia lair, detective, doctor).
- Ensure scene scaling, camera presets, and lighting per scene.
- Complete reasoning display (omniscient-only, selective reveal).
- Validate full playback across v1.3 logs.

### Phase 11: Production Readiness
- TTS audio sync + controls.
- Export workflow (timeline + cut points + metadata).
- Character reactions/gestures + idle variation.
- UI polish, accessibility, and performance tuning.

## Mid Term (Post-Phase 11)

### Tournaments + Persistent Memory
- Multi-game series with fixed roster.
- Cross-game memories per opponent (guardrails against role leakage).
- Tournament scoring + standings.

### Narrator System
- Flavor commentary only (no paraphrasing player speech).
- Optional for MVP; on by default for content production.

### Evaluation Framework
- Beyond win rate: tension, deception success, surprise reveals.
- Manual evaluation sets + A/B tests for persona variants.

## Longer Term

### Additional Roles (Beyond Doctor)
- Don/Godfather, Jester, or other roles after balance testing.
- Clear rule changes and prompt adjustments per role.

### Competition Platform
- Persona submissions on a fixed model.
- Ranked ladder and seasonal tournaments.

### Live / Streaming Mode
- Real-time playback with commentary.
- Viewer controls tuned for live pacing.
