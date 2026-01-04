# Project Progress

Single source of truth for delivery status and next steps.

## Status

**Game Engine:** Core complete (Phases 1-8), Phase 9 in progress (9.1–9.6 done; 9.7 pending)
**Replay Viewer:** In Progress (Phase 10 - Stylized Mesh)

### Completed Phases

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Project foundation (schemas, config) | ✅ |
| Phase 2 | LLM provider layer | ✅ |
| Phase 3 | Game state & event system | ✅ |
| Phase 4 | Context builder | ✅ |
| Phase 5 | Player agent | ✅ |
| Phase 6 | Game loop (first runnable game) | ✅ |
| Phase 7 | Quality and observability | ✅ |
| Phase 8 | Replayable logs (schema v1.3) | ✅ |
| **Phase 9** | **Roster + Role Expansion (Engine)** | 🚧 IN PROGRESS |
| **Phase 10** | **3D Stylized Mesh Viewer** | 🚧 IN PROGRESS |

## Current Focus: Phase 9 + Phase 10

Expanding the engine roster/roles (Phase 9, tests + viewer sync pending) and building the
stylized mesh viewer (Phase 10).
See `tasks/phase9.md` and `tasks/phase10.md` for detailed plans.

**Key decisions:**
- Visual style: Stylized mesh, Roblox-adjacent (not voxel)
- Tech stack: React Three Fiber + drei + Zustand
- Character system: Stylized mesh characters (GLB), 2-3 iconic features
- Voting display: Sequential, show who voted for who
- Reasoning: Curated (Detective always, Mafia rotating)

---

## Priorities (P0 / P1 / P2)

**P0 — Essentials (Week 1)**
- Finish character roster (current 10 personas) and load GLBs in viewer
- Build town square + mafia lair scene GLBs; load in viewer
- Apply scene scaling/centering + offsets to all scenes
- Camera presets + lighting tuning per scene (day/night/mafia/detective)

**P1 — Watchability (Week 1.5-2)**
- Basic TTS playback with 10 unique voices + volume/speed controls
- Reasoning display (10.6) + timeline scrubber + keyboard shortcuts
- Scene atmosphere pass (fog, lamps/props) where needed

**P2 — Polish (Week 2+)**
- Character reactions/gestures + idle variation
- Timeline/cut-point exports + editor workflow docs
- Accessibility + performance tuning

---

## Documentation

| Document | Purpose |
|----------|---------|
| `docs/replay_vision.md` | Visual style, narrative flow, viewer experience |
| `docs/engine_foundations.md` | Engine architecture and invariants (Phases 1-9) |
| `tasks/phase10.md` | Current phase implementation details |
| `tasks/phase1.md` - `tasks/phase8.md` | Completed game engine phases |

## Roadmap

See `tasks/roadmap.md` for forward-looking plans beyond the current phases.
