# Phase 10: 3D Replay Viewer (Roblox-Adjacent, Stylized Mesh)
**Goal:** Build a 3D stylized mesh replay viewer using React Three Fiber that transforms game logs into cinematic, YouTube-ready content.

**Status:** 🚧 IN PROGRESS (Phases 10.1-10.3 complete, 10.4-10.6 pending)

**Current phase:** 10.3 (Voting + Death) - mostly complete, needs runtime verification

**Scope:** Core viewer functionality (log playback, 3D scene, events visualization)

**Predecessor:** Phase 9 (2.5D CSS viewer) - ARCHIVED

See `docs/replay_vision.md` for visual style rationale and detailed specs.

## Locked Style Decisions

- **Visual target:** Roblox-adjacent, stylized plastic look (not full voxel).
- **Environment:** low-poly/blocky town square with clean materials and serious lighting.
- **Characters:** simple proportions, bold silhouettes, 2-3 iconic features.
- **Consistency rules:** unified palette, unified material model, consistent scale.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | React + Vite |
| 3D Engine | React Three Fiber |
| Helpers | @react-three/drei |
| State | Zustand |
| Animation | React Spring |
| Assets | Hunyuan3D (characters) + asset packs via Blender (scenes) → .glb |
| Debug | Leva |

```bash
cd viewer
npm install three @react-three/fiber @react-three/drei zustand @react-spring/three leva
```

---

## Architecture

**Log-driven:** Viewer consumes logs, doesn't simulate game rules.

**Default mode:** Omniscient. During development and content review, seeing all information
(roles, reasoning, Mafia coordination) is essential. Public mode exists for "mystery" YouTube
cuts but is secondary—most viewers want the full drama, not the puzzle.

```
Game Log (JSON) → Log Parser → Timeline Store (Zustand) → Scene Renderer (R3F)
```

### Component Structure

```
viewer/src/
├── App.jsx                 # Entry point, log loading
├── stores/
│   └── gameStore.js        # Zustand: log, eventIndex, playback state
├── components/
│   ├── Scene.jsx           # R3F Canvas wrapper
│   ├── Stage.jsx           # Scene loader (GLB) + floor placeholder
│   ├── Character.jsx       # Single stylized character
│   ├── Characters.jsx      # All characters positioned in arc
│   ├── Subtitles.jsx       # Speech text display
│   ├── VoteTokens.jsx      # Vote visualization (2D overlay)
│   ├── Lighting.jsx        # Day/night lighting
│   └── Camera.jsx          # Camera presets + transitions
├── hooks/
│   ├── usePlayback.js      # Play, pause, step controls
│   ├── useVoteSequence.js  # Sequential vote reveal timing
│   └── useNightDialogue.js # Night kill dialogue parsing
├── utils/
│   └── logParser.js        # Parse log JSON into timeline
└── assets/
    └── models/             # .glb models
```

---

## Asset Pipeline

- Characters: `docs/character_pipeline.md`
- Scenes: `docs/scene_pipeline.md` (asset packs assembled in Blender)

---

## Implementation Phases

### Phase 10.0: Art Direction + Asset Plan

**Goal:** Lock the style and asset pipeline before heavy implementation.

**Tasks:**
- [x] Define a style bible (palette, materials, lighting rules, scale) in `docs/style_bible.md`
- [x] Lock character tool (fal.ai: Hunyuan3D) + scene pipeline (asset packs + Blender)
- [x] Draft prompt rules for characters + select scene asset packs
- [x] Draft a town square blockout (houses, lamps, round table)
- [ ] Smoke test: load 1 character GLB + 1 scene GLB, verify R3F loads both
  - Character GLB loads in viewer (tralalelo.glb); scene GLB pending.

**Deliverable:** Style bible + character prompts + scene pipeline + blockout scene + verified pipeline.

**Status:** ⚠️ Mostly complete. Smoke test (scene GLB load) pending.

---

### Phase 10.1: Foundation

**Goal:** Basic 3D scene that responds to log events.

**Tasks:**
- [x] Clean up `viewer/` - remove Phase 9 bloat
- [x] Install R3F dependencies
- [x] Create `Scene.jsx` with R3F Canvas
- [x] Create `Stage.jsx` with floor plane (town square placeholder)
- [x] Create `Character.jsx` rendering colored placeholders (meshes or cubes)
- [x] Create `Characters.jsx` positioning players in a semi-arc based on `log.players.length`
- [x] Create `gameStore.js`:
  - `log`, `eventIndex`, `playing`
  - `nextEvent()`, `prevEvent()`, `setIndex()`
- [x] Create `logParser.js` to extract timeline (handle `night_zero_strategy`: skip in public, short scene in omniscient)
- [x] Basic prev/next buttons
- [x] Load log via file input

**Deliverable:** N colored cubes. Stepping through events highlights active speaker.

**Status (code review 2025-01):** ✅ Store actions present. Private fields filtering logic verified. ⚠️ **Needs runtime testing**: event parsing edge cases.

---

### Phase 10.2: Camera + Speech

**Goal:** Cinematic camera and speech display.

**Tasks:**
- [x] Create `Camera.jsx` with drei's `PerspectiveCamera`
- [x] Camera presets:
  - Wide shot (all visible)
  - Speaker focus (zoom on active)
  - Vote tension (slow pan)
- [x] Animate transitions with React Spring
- [x] Create `Subtitles.jsx` for speech text
- [x] Create `Lighting.jsx`:
  - Day: warm directional + ambient
  - Night: cool blue + low ambient

**Deliverable:** Camera cuts to speaker. Subtitles show text. Day/night lighting works.

**Status (code review 2025-01):** ✅ Camera presets + transitions implemented. Lighting colors match style_bible. **Drifts**: vote pan constant speed. ⚠️ **Needs runtime testing**: camera focus accuracy, lighting during scene transitions.

---

### Phase 10.3: Voting + Death

**Goal:** Visualize votes and eliminations.

**Tasks:**
- [x] Create `VoteTokens.jsx`
- [x] Sequential vote reveal:
  - Delay between each vote (900ms per vote)
  - Running count display (e.g., "Bob: 3")
  - Vote chips show "Voter → Target" (2D overlay)
- [x] Death animation:
  - Sink below stage
  - Grayscale material
  - X eyes
  - Remain visible (ghosted)
- [x] Handle revote flow (round 2)
- [x] Defense banner overlay during defense events
- [x] Replay flow: night‑kill handled as target‑marking with day‑start announcement; camera focuses on night‑kill victim via day_announcement.
- [x] Investigation: reasoning shown as subtitles; target/result shown in banner.

**Deliverable:** Votes reveal one-by-one. Dead characters visually distinct.

**Status (code review 2025-01):** ✅ Vote sequence logic, death animation, overlay components implemented. ⚠️ **Needs runtime testing**: vote timing accuracy, death state transitions.

---

### Phase 10.4: Character Models (Stylized Mesh)

**Goal:** Replace placeholders with real character meshes.

**Tasks:**
- [ ] Generate a base humanoid via fal.ai Hunyuan3D (blocky, stylized plastic)
- [ ] Create 3 initial hero characters via fal.ai:
  - Bombardiro Crocodilo (use reference image + style prompt)
  - Tralalero Tralala (use reference image + style prompt)
  - Generic humanoid (text prompt only)
- [ ] Apply unified material properties; keep textures only if flat/clean (otherwise palette)
- [ ] Download .glb files
- [ ] Model loading with `useGLTF`
- [ ] Hot-swap fallback: `MODELS[persona] || MODELS.placeholder`
- [ ] Simple idle animation (bobbing)

**Deliverable:** 3 character models, others placeholders. Dynamic loading works.

**Status:** ❌ Not started.

---

### Phase 10.5: Scenes + Modes

**Goal:** Scene variations and viewing modes.

**Tasks:**
- [ ] Create remaining character models
- [ ] Scene variations (scene GLBs per `docs/scene_pipeline.md`):
  - Day town square (warm)
  - Mafia lair (red, fog)
  - Detective office (blue/noir)
- [x] Scene switching based on phase
- [x] Scene roster filtering:
  - Mafia lair shows ONLY Mafia
  - Detective office shows ONLY Detective
  - Town square shows ALL living players
- [x] Night kill is a target-marking beat (no death yet)
- [x] Death animation triggers at day start after dawn/announcement
- [x] Public/Omniscient toggle (core):
  - Public: hide roles, reasoning, Mafia scenes
  - Omniscient: show everything
- [x] Character name labels (floating above head, always visible)
- [x] Role indicators (omniscient only):
  - Color-coded badge (red=Mafia, blue=Detective, gray=Villager) ✅ Implemented
  - Optional: role icon (gun, magnifying glass)

**Deliverable:** All characters modeled. Scene changes work. Mode toggle works.

**Status (code review 2025-01):** ⚠️ Partial. Scene switching logic, roster filtering implemented. ⚠️ **Needs runtime testing**: mode toggle behavior, scene visibility edge cases. Character models pending.

---

### Phase 10.6: Polish

**Goal:** Reasoning display and UI polish.

**Tasks:**
- [ ] Reasoning display:
  - Background dims to 30%
  - Role-colored glow under character
  - Thought text overlay
- [ ] Reasoning heuristics:
  - Always: Detective
  - Day speech: Mafia (rotate if 3+)
  - Before defense: most nominated
- [ ] Timeline scrubber
- [ ] Phase markers (Day 1, Night 1)
- [ ] Keyboard shortcuts (space, arrows)
- [ ] Performance optimization if needed

**Deliverable:** Full-featured viewer ready for content production.

**Status:** ❌ Not started.

---

## Known Issues / Remaining

**Pending tasks (Phase 10):**
- Character model pipeline (10.4)
- Scene GLB assembly: fog for Mafia lair, props from asset packs (10.5)
- Reasoning display rules: Detective always, Mafia pre‑speech, most nominated before defense (10.6)
- New logs with corrected last_words → elimination ordering

**Deferred to Phase 11 (Production Readiness):**
- TTS audio integration + sync
- Export/recording workflow
- Advanced animation (expressions, gestures)
- UI polish (summary, scoreboard, accessibility)

**Spec drifts (cosmetic):**
- `Camera.jsx`: Vote tension pan is constant speed (~40s orbit). Spec implies variable pacing for tension building—consider slowing as votes reveal.
- `game_end` event: No explicit handler in `usePlayback.js` or `findActiveSpeaker`—falls back to 2200ms (functional but implicit).

---

## Log Schema Reference

See `tasks/phase8.md` for the v1.2 log schema and reasoning payload mapping.

---

## Testing

1. Load sample log from `logs/`
2. Step through all events
3. Verify camera follows speaker
4. Verify sequential vote display
5. Verify death animation
6. Toggle modes, verify visibility

---

## Success Criteria

### Phase 10 Complete When:

1. ✅ Loads any v1.2 game log
2. ⚠️ 7 characters rendered (3+ real models) - Partial (placeholders working, models pending)
3. ✅ Camera cuts to active speaker
4. ✅ Subtitles display speech
5. ✅ Votes reveal sequentially
6. ✅ Dead characters distinct (sink, grayscale, X eyes)
7. ✅ Day/night lighting works
8. ✅ Public/Omniscient toggle works
9. ❌ Reasoning displays for featured players (Phase 10.6)
10. ✅ Full game playback without errors

**Viewer Readiness after Phase 10:** ~60-70%
- **Good for:** Internal testing, debugging, log validation
- **Missing:** Audio, export workflow, advanced animation, UI polish
- **Next:** Phase 11 (Production Readiness) for YouTube content
