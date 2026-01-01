# Phase 10: 3D Voxel Replay Viewer

**Goal:** Build a 3D voxel-style replay viewer using React Three Fiber that transforms game logs
into cinematic, YouTube-ready content.

**Status:** 🚧 IN PROGRESS

**Predecessor:** Phase 9 (2.5D CSS viewer) - ARCHIVED

See `docs/replay_vision.md` for visual style rationale and detailed specs.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | React + Vite |
| 3D Engine | React Three Fiber |
| Helpers | @react-three/drei |
| State | Zustand |
| Animation | React Spring |
| Assets | MagicaVoxel → .glb |
| Debug | Leva |

```bash
cd viewer
npm install three @react-three/fiber @react-three/drei zustand @react-spring/three leva
```

---

## Architecture

**Log-driven:** Viewer consumes logs, doesn't simulate game rules.

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
│   ├── Stage.jsx           # Floor, table geometry
│   ├── Character.jsx       # Single voxel character
│   ├── Characters.jsx      # All characters positioned in arc
│   ├── Subtitles.jsx       # Speech text display
│   ├── VoteTokens.jsx      # Vote visualization
│   ├── Lighting.jsx        # Day/night lighting
│   └── Camera.jsx          # Camera presets + transitions
├── hooks/
│   └── usePlayback.js      # Play, pause, step controls
├── utils/
│   └── logParser.js        # Parse log JSON into timeline
└── assets/
    └── models/             # .glb voxel models
```

---

## Implementation Phases

### Phase 10.1: Foundation

**Goal:** Basic 3D scene that responds to log events.

**Tasks:**
- [ ] Clean up `viewer/` - remove Phase 9 bloat
- [ ] Install R3F dependencies
- [ ] Create `Scene.jsx` with R3F Canvas
- [ ] Create `Stage.jsx` with floor plane
- [ ] Create `Character.jsx` rendering colored cubes (placeholders)
- [ ] Create `Characters.jsx` positioning players in a semi-arc based on `log.players.length`
- [ ] Create `gameStore.js`:
  - `log`, `eventIndex`, `playing`
  - `nextEvent()`, `prevEvent()`, `setIndex()`
- [ ] Create `logParser.js` to extract timeline (handle `night_zero_strategy`: skip in public, optional omniscient stub)
- [ ] Basic prev/next buttons
- [ ] Load log via file input

**Deliverable:** N colored cubes. Stepping through events highlights active speaker.

---

### Phase 10.2: Camera + Speech

**Goal:** Cinematic camera and speech display.

**Tasks:**
- [ ] Create `Camera.jsx` with drei's `PerspectiveCamera`
- [ ] Camera presets:
  - Wide shot (all visible)
  - Speaker focus (zoom on active)
  - Vote tension (slow pan)
- [ ] Animate transitions with React Spring
- [ ] Create `Subtitles.jsx` for speech text
- [ ] Create `Lighting.jsx`:
  - Day: warm directional + ambient
  - Night: cool blue + low ambient

**Deliverable:** Camera cuts to speaker. Subtitles show text. Day/night lighting works.

---

### Phase 10.3: Voting + Death

**Goal:** Visualize votes and eliminations.

**Tasks:**
- [ ] Create `VoteTokens.jsx`
- [ ] Sequential vote reveal:
  - Delay between each vote
  - Token animation to target
  - Running count display
- [ ] Death animation:
  - Sink below stage
  - Grayscale material
  - X eyes
- [ ] Handle revote flow

**Deliverable:** Votes reveal one-by-one. Dead characters visually distinct.

---

### Phase 10.4: Voxel Characters

**Goal:** Replace cubes with real voxel models.

**Tasks:**
- [ ] Create 3 initial models in MagicaVoxel:
  - Bombardiro Crocodilo
  - Tralalero Tralala
  - Generic humanoid
- [ ] Export as .glb
- [ ] Model loading with `useGLTF`
- [ ] Hot-swap fallback: `MODELS[persona] || MODELS.placeholder`
- [ ] Simple idle animation (bobbing)

**Deliverable:** 3 voxel models, others cubes. Dynamic loading works.

---

### Phase 10.5: Scenes + Modes

**Goal:** Scene variations and viewing modes.

**Tasks:**
- [ ] Create remaining character models
- [ ] Scene variations:
  - Day (warm parlor)
  - Mafia lair (red, fog)
  - Detective office (blue/noir)
- [ ] Scene switching based on phase
- [ ] Public/Omniscient toggle:
  - Public: hide roles, reasoning, Mafia scenes
  - Omniscient: show everything
- [ ] Role badges (Mafia gun, Detective badge)

**Deliverable:** All characters modeled. Scene changes work. Mode toggle works.

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

---

## File Changes

**Delete:**
- `viewer/src/App.jsx` (replace)
- `viewer/src/index.css` (replace with minimal)

**Keep:**
- `viewer/package.json` (update deps)
- `viewer/vite.config.js`
- `viewer/index.html`
- `viewer/public/`

**Create:**
- `viewer/src/stores/`
- `viewer/src/components/`
- `viewer/src/hooks/`
- `viewer/src/utils/`
- `viewer/src/assets/models/`

---

## Log Schema (v1.1)

Required fields:

```javascript
log.schema_version
log.game_id
log.timestamp_start
log.timestamp_end
log.winner
log.players           // [{seat, persona_id, name, role, outcome}]
log.events            // [{type, timestamp, data, private_fields}]

event.type            // "speech", "vote", "night_kill", etc.
event.timestamp       // ISO8601
event.data.phase      // "day_1", "night_1", etc.
event.data.round_number
event.data.stage
event.data.state_public    // {phase, round_number, living, dead, nominated}
event.private_fields // list of data keys hidden in public mode
event.data.reasoning // present in omniscient view when not filtered
```

Notes:
- `state_before`/`state_after` live inside `event.data` for roster-changing events.
- Private reasoning is in `event.data.reasoning` and listed in `event.private_fields`.

No log changes needed.

---

## Assets

### Characters (Priority)

| Persona | Description |
|---------|-------------|
| Bombardiro Crocodilo | Green croc, bomber jacket |
| Tralalero Tralala | Blue shark, cheerful |
| Generic humanoid | Placeholder for others |

### Props

| Prop | Scene |
|------|-------|
| Round table | Day + Mafia |
| Chairs | All |
| Fog particles | Mafia lair |

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

Phase 10 complete when:

1. Loads any v1.1 game log
2. 7 characters rendered (3+ real models)
3. Camera cuts to active speaker
4. Subtitles display speech
5. Votes reveal sequentially
6. Dead characters distinct
7. Day/night lighting works
8. Public/Omniscient toggle works
9. Reasoning displays for featured players
10. Full game playback without errors
