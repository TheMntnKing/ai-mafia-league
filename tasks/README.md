# Project Progress

Single source of truth for delivery status and next steps.

## Status

**Game Engine:** Complete (Phases 1-8)
**Replay Viewer:** In Progress (Phase 10 - 3D Voxel)

### Completed Phases

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Project foundation (schemas, config, database) | ✅ |
| Phase 2 | LLM provider layer | ✅ |
| Phase 3 | Game state & event system | ✅ |
| Phase 4 | Context builder | ✅ |
| Phase 5 | Player agent | ✅ |
| Phase 6 | Game loop (first runnable game) | ✅ |
| Phase 7 | Quality and observability | ✅ |
| Phase 8 | Replayable logs (schema v1.2) | ✅ |
| Phase 9 | 2.5D CSS Viewer | ⚠️ ARCHIVED |
| **Phase 10** | **3D Voxel Viewer** | 🚧 IN PROGRESS |

### Phase 9 Archived

The 2.5D CSS-based viewer (Phase 9) has been archived. We're starting fresh with a 3D voxel
approach using React Three Fiber. See `docs/replay_vision.md` for rationale.

The `viewer/` directory will be cleaned up and rebuilt for Phase 10.

---

## Current Focus: Phase 10

Building a 3D voxel-style replay viewer. See `tasks/phase10.md` for detailed plan.

**Key decisions:**
- Visual style: 3D Voxel (Minecraft/Roblox aesthetic)
- Tech stack: React Three Fiber + drei + Zustand
- Character system: Voxel blocks with iconic accessories
- Voting display: Sequential, show who voted for who
- Reasoning: Curated (Detective always, Mafia rotating)

**Milestones:**
1. Foundation: Cubes + event playback (Week 1-2)
2. Camera + Speech bubbles (Week 2-3)
3. Voting + Death animations (Week 3-4)
4. First voxel character models (Week 4-5)
5. Full character set + scenes (Week 5-6)
6. Polish + reasoning display (Week 6+)

---

## Documentation

| Document | Purpose |
|----------|---------|
| `docs/replay_vision.md` | Visual style, narrative flow, viewer experience |
| `tasks/phase10.md` | Current phase implementation details |
| `tasks/phase1-8.md` | Completed game engine phases |

---

## Post-MVP Ideas

### Game Engine Enhancements
- 10 players with 3 Mafia (coordination redesign needed)
- Power roles: Doctor, Jester, Godfather
- Additional LLM providers (Gemini, OpenAI)
- Tournament mode with persistent memory
- Narrator system

### Viewer Enhancements
- TTS integration (ElevenLabs)
- Video export directly from viewer
- Timeline markers for "high drama" moments
- Live streaming mode
- Mobile support

### Content Pipeline
- Persona roster expansion (memes, historical figures, presidents)
- YouTube channel setup
- Editing workflow documentation
- Community persona submissions
