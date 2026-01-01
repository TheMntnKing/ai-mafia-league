# Phase 10: 3D Replay Viewer (Roblox-Adjacent, Stylized Mesh)

**Goal:** Build a 3D voxel-style replay viewer using React Three Fiber that transforms game logs into cinematic, YouTube-ready content.

**Status:** 🚧 IN PROGRESS

**Predecessor:** Phase 9 (2.5D CSS viewer) - ARCHIVED

See `docs/replay_vision.md` for visual style rationale and detailed specs.

## Locked Style Decisions

- **Visual target:** Roblox-adjacent, stylized plastic look (not full voxel).
- **Environment:** low-poly/blocky town square with clean materials and serious lighting.
- **Characters:** stylized mesh avatars with simple proportions and bold silhouettes.
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
| Assets | fal.ai API (Hunyuan3D, Trellis 2) → .glb |
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
│   ├── Stage.jsx           # Floor, table geometry
│   ├── Character.jsx       # Single stylized character
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
    └── models/             # .glb models
```

---

## Asset Strategy (AI-Generated via API)

**Goal:** Fast iteration with a consistent, meme-friendly visual style.

**Style target:** Stylized plastic/low-poly town + stylized mesh characters (Roblox-adjacent).
Keep one palette, one material model, and consistent scale.

### Primary Tools (fal.ai Pay-Per-Use)

| Tool | Use Case | Cost | Link |
|------|----------|------|------|
| **Hunyuan3D v2** | Characters, complex props | ~$0.20-0.30/gen | [fal.ai](https://fal.ai/models/fal-ai/hunyuan3d/v2) |
| **Trellis 2** | Props, scene elements | $0.25-0.35/gen | [fal.ai](https://fal.ai/models/fal-ai/trellis-2) |

**Why API over SaaS subscriptions:**
- Pay-per-use (~$5-10 for all assets) vs $17+/month subscriptions
- Same underlying models
- No commitment, scale as needed

### Prompt Rules (Apply to All AI Assets)

**Characters (Hunyuan3D)**
- Style: "stylized plastic", "blocky", "toy-like", "clean silhouette"
- Proportions: big head, chunky limbs, minimal facial detail
- Materials: solid colors, no photo textures, no micro-detail
- Pose: A-pose for potential rigging
- Input: Reference image + style keywords (models don't know meme names)

**Props/Scenes (Trellis 2 or Hunyuan3D)**
- Style: low-poly, clean shapes, simple forms
- Materials: flat colors or minimal gradients, no noisy textures
- Modularity: separate props (lamps, benches, signs) for reuse

**Consistency Pass (Required)**
- Override all materials to the project palette in-engine
- Normalize scale (target ~1.7m for humanoid height)
- Center/pivot at feet for characters, base for props

---

## Implementation Phases

### Phase 10.0: Art Direction + Asset Plan

**Goal:** Lock the style and asset pipeline before heavy implementation.

**Tasks:**
- [x] Define a style bible (palette, materials, lighting rules, scale) in `docs/style_bible.md`
- [x] Lock AI tools (fal.ai: Hunyuan3D for characters, Trellis 2 for props)
- [x] Draft prompt rules for town assets + character silhouettes
- [x] Draft a town square blockout (houses, lamps, round table)
- [ ] Smoke test: generate 1 character + 1 prop via fal.ai, verify GLB loads in R3F

**Deliverable:** Style bible + AI prompt rules + blockout scene + verified pipeline.

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

### Phase 10.4: Character Models (Stylized Mesh)

**Goal:** Replace placeholders with real character meshes.

**Tasks:**
- [ ] Generate a base humanoid via fal.ai Hunyuan3D (blocky, stylized plastic)
- [ ] Create 3 initial hero characters via fal.ai:
  - Bombardiro Crocodilo (use reference image + style prompt)
  - Tralalero Tralala (use reference image + style prompt)
  - Generic humanoid (text prompt only)
- [ ] Apply unified materials/palette (override textures if needed)
- [ ] Download .glb files
- [ ] Model loading with `useGLTF`
- [ ] Hot-swap fallback: `MODELS[persona] || MODELS.placeholder`
- [ ] Simple idle animation (bobbing)

**Deliverable:** 3 character models, others placeholders. Dynamic loading works.

---

### Phase 10.5: Scenes + Modes

**Goal:** Scene variations and viewing modes.

**Tasks:**
- [ ] Create remaining character models
- [ ] Scene variations:
  - Day town square (warm)
  - Mafia lair (red, fog)
  - Detective office (blue/noir)
- [ ] Scene switching based on phase
- [ ] Scene roster filtering:
  - Mafia lair shows ONLY Mafia
  - Detective office shows ONLY Detective
  - Town square shows ALL living players
- [ ] Night kill is a target-marking beat (no death yet)
- [ ] Death animation triggers at day start after dawn/announcement
- [ ] Public/Omniscient toggle (core):
  - Public: hide roles, reasoning, Mafia scenes
  - Omniscient: show everything
- [ ] Character name labels (floating above head, always visible)
- [ ] Role indicators (omniscient only):
  - Color-coded badge or underline (red=Mafia, blue=Detective, gray=Villager)
  - Optional: role icon (gun, magnifying glass)

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

## Log Schema (v1.2)

Required fields:

```javascript
log.schema_version
log.game_id
log.timestamp_start
log.timestamp_end
log.winner
log.players           // [{seat, persona_id, name, role, outcome}]
log.events            // [{type, timestamp, data, private_fields}]

event.type            // "speech", "vote_round", "elimination", "night_kill", etc.
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
- `vote_round` includes `data.round`, `data.outcome`, and `data.votes`.
- `vote_round.data.outcome`: `"eliminated"`, `"no_elimination"`, or `"tie"` (round 1 only).
- `elimination` includes `data.eliminated`.

**Reasoning payloads (viewer mapping):**
Use `thought` for internal monologue TTS (plays before spoken line) and `subtitle` for the
spoken line. Many events have no subtitle.

| event.type | thought source | subtitle source | notes |
|-----------|----------------|-----------------|-------|
| `speech` | `data.reasoning.reasoning` | `data.text` | `data.reasoning` is full `SpeakingOutput`. |
| `defense` | `data.reasoning.reasoning` | `data.text` | `data.reasoning` is full `DefenseOutput`. |
| `last_words` | `data.reasoning.reasoning` | `data.text` | `data.reasoning` is full `LastWordsOutput`. |
| `night_zero_strategy` | `data.reasoning.reasoning` | `data.text` | `data.reasoning` is full `SpeakingOutput` (night_zero context). |
| `vote_round` | `data.vote_details[<voter>].reasoning` | none | Per-voter `VotingOutput`. Use selectively. |
| `night_kill` | see notes | `proposal_details*[*].message` (optional) | Reasoning is a coordination bundle. |
| `investigation` | `data.reasoning.reasoning` | none | `data.reasoning` is full `InvestigationOutput`. |
| `elimination` | none | none | Use UI + day announcement, not log text. |

**Night kill bundle details:**
- Round 1: `reasoning.proposals` + `reasoning.proposal_details`
- Round 2: `reasoning.proposals_r1`, `reasoning.proposals_r2`,
  `reasoning.proposal_details_r1`, `reasoning.proposal_details_r2`, optional `decided_by`
- Each entry in `proposal_details*` is a full `NightKillOutput` (includes `message` and
  `reasoning`). Viewer must parse these; do not assume `data.text` exists.

Viewer should handle `vote_round` + `elimination` events (schema v1.2).

---

## Assets

### Characters (Priority)

| Persona | Description |
|---------|-------------|
| Bombardiro Crocodilo | Green croc, bomber jacket |
| Tralalero Tralala | Blue shark, cheerful |
| Generic humanoid | Placeholder for others |

### Scene Targets (Town)

| Prop | Scene |
|------|-------|
| Round table | Day + Mafia |
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

1. Loads any v1.2 game log
2. 7 characters rendered (3+ real models)
3. Camera cuts to active speaker
4. Subtitles display speech
5. Votes reveal sequentially
6. Dead characters distinct
7. Day/night lighting works
8. Public/Omniscient toggle works
9. Reasoning displays for featured players
10. Full game playback without errors
