# Replay Vision

Source of truth for the AI Mafia replay viewer.

## Goal

Transform raw game logs into a **cinematic, TV-quality narrative**. The replay should feel like
watching a mystery thriller (Public Mode) or a psychological drama (Omniscient Mode) - not like
debugging code or reading transcripts.

**Target platform:** YouTube (15-30 minute episodes)
**Target feel:** Entertainment first, strategic depth optional
**Log requirement:** Viewer expects v1.3 logs only (no backward compatibility).

---

## Visual Style: Stylized Mesh (Not Voxel)

Stylized mesh humanoids with blocky proportions. Roblox-adjacent silhouette, not voxel.

**Rationale:**
- Universal character system - blocky silhouettes work for any persona (memes, presidents, historical figures)
- Scene variety - distinct environments for day/night/Mafia lair
- YouTube-ready - strong thumbnails, animation capability, premium feel
- Meme culture native - familiar aesthetic to target audience

### Asset Pipeline (Practical)
- Character + scene workflow: `docs/viewer/art_pipeline.md`
- Output: `.glb` for R3F (scale normalized, pivot at feet, materials optionally overridden)
  - Scenes are auto-centered/scaled in viewer; tune per scene if needed

---

## Viewing Modes

**Default: Omniscient.** Most viewers want the full drama—seeing who's lying, watching
Mafia coordinate, feeling the Detective's uncertainty. Public mode is for rare "mystery"
cuts where the audience guesses along.

### Omniscient Mode (Drama) — Default
- Shows: everything—roles, curated reasoning, Mafia night scenes, Detective investigations
- Night: full scenes (Mafia lair, Detective office)
- Hook: "Watch the perfect lie unfold."
- Character labels: name + role indicator (color-coded)

### Public Mode (Mystery)
- Shows: speeches, nominations, votes, deaths
- Hides: roles, reasoning, Mafia coordination, investigation results
- Night: quick fade transition only
- Hook: "Who is Mafia? Figure it out before the reveal."
- Character labels: name only (no role)

---

## Day Phase Flow

1. **Night kill announced** (if any) - no last words for night kills
2. **Discussion** - each player speaks in seat order (rotating each day)
   - Camera focuses on speaker
   - TTS audio with subtitles
   - Omniscient: reasoning shown before speech for featured players
   - Each player nominates someone
3. **Voting** - sequential reveal, one vote at a time with running count
   - Shows who voted for who, not just totals
4. **Tie resolution** (if needed) - defense speeches, then revote
5. **Elimination** (if any) - last words, then death animation
6. **Transition to night**

---

## Night Phase Flow

### Public Mode
Brief transition only:
1. "Night falls" fade (2-3 sec)
2. Optional sleeping town shot (2-3 sec)
3. Dawn transition

### Omniscient Mode
Full scenes:
1. Night falls transition
2. Mafia lair - red lighting, show coordination (each Mafia speaks), target highlight (marked, not dead)
3. Doctor scene - protection choice with shield glow on target
4. Detective scene - investigation target and result
5. Dawn transition (return to town square)
6. Day announcement: "X was killed" or "No one died" → death animation plays now (if any)

### Night Zero
Mafia coordinate but don't kill. Detective doesn't act.

- **Public:** Skip entirely or brief title card
- **Omniscient:** Optional Mafia planning scene

**Recommendation:** Keep in engine for gameplay. Viewer can skip or minimize.
**Log note:** Night Zero emits `night_zero_strategy` events with private fields; public mode can
ignore these, omniscient can optionally show a short Mafia scene.

---

## Scene Visibility & Death Timing (Viewer Rules)

**Scene roster:**
- Mafia lair: ONLY Mafia visible (3 Mafia in 10-player games)
- Doctor scene: ONLY Doctor visible
- Detective office: ONLY Detective visible
- Town square (day): ALL living players visible

**Night events do NOT kill the target.** The target is only marked during night scenes.

**Death timing:** Death animation happens at **day start** (after dawn transition and announcement),
not during night events. The `night_resolution` event determines if kill was blocked by Doctor.

**Scene switching logic (omniscient):**
- `phase = night_*` → transition to night scene
- `night_zero_strategy` / `mafia_discussion` / `mafia_vote` → Mafia lair
- `doctor_protection` → Doctor scene
- `investigation` → Detective office
- `night_resolution` → (internal, no scene change)
- `phase = day_*` → town square (announce result, then play death animation if any)

---

## Voting Display

Sequential reveal with running count:
```
Alice votes for Bob → Bob: 1
Charlie votes for Bob → Bob: 2
Diana votes Skip → Bob: 2, Skip: 1
Eve votes for Bob → Bob: 3 - ELIMINATED
```

Shows social dynamics and builds tension.

---

## Reasoning Display

Don't show everyone - cognitive overload. Feature selectively:

| Player | When |
|--------|------|
| Detective | Always (they're solving the puzzle) |
| Mafia | Before day speech (the lie reveal) |
| Most nominated | Before defense speech |
| About to die | Final thoughts |

**3+ Mafia:** Rotate which Mafia is featured each day.

**Log note:** In omniscient mode, reasoning text should be sourced from
`event.data.reasoning` (it appears in `event.private_fields` for public filtering).
Public mode ignores private fields.

**Visual treatment:**
1. Background dims to ~30%
2. Role-colored glow pulses under character (red=Mafia, blue=Detective)
3. Thought text overlay
4. 2-3 seconds, then transition to speech

---

## Pacing

Target word counts (vary with player count):

| Action | Words |
|--------|-------|
| Day Speech | 50-80 |
| Reasoning | 30-50 |
| Defense | 30-50 |
| Last Words | 40-80 |
| Mafia Night Chat | 30-50 |

Game length: 10 players ~25-35 min (with Doctor saves potentially extending games).

---

## Audio

**TTS:** Part of game engine. Each speech generates audio file. Each persona has distinct voice.

**Subtitles:** Rendered in viewer or added in editing. No 3D speech bubbles.

**Music/SFX:** Added in editing.

---

## Character Design

Each persona = stylized mesh humanoid + 2-3 iconic features:
- **Head shape:** Round, animal snout, cube, etc.
- **Hair/headwear:** Distinctive silhouette element
- **Accessories:** Glasses, props, badges
- **Color scheme:** Recognizable at thumbnail size

Material, pose, palette, and lighting rules live in `docs/viewer/art_pipeline.md`.

**Dead state:** Grayscale, X eyes, sink below stage. Stay visible (ghosted).


---

## Scenes

| Scene | Lighting | Usage |
|-------|----------|-------|
| Day (Town Square) | Warm, golden hour | Discussion + voting |
| Night (Sleeping) | Blue/dark, moonlight | Transition (public mode) |
| Mafia Lair | Red underglow, fog | Night coordination (omniscient) |
| Doctor Scene | Green/teal accent, medical | Protection choice (omniscient) |
| Detective Office | Neutral + warm accent | Investigation (omniscient) |

**Layout:** Characters in semi-circle arc facing camera. Table/podium in foreground.

**Doctor Scene Notes:**
- Only Doctor visible
- Protection target highlighted with shield/glow effect
- Brief scene (~5 sec) - Doctor chooses, protection animation
- No confirmation whether protection was successful (resolved at dawn)

---

## Implementation Notes

- Log-driven playback; no rules simulation.
- Public mode hides `private_fields`; omniscient shows all roles and reasoning.
- Component/stack details live in `tasks/phase10.md`.

---

## Viewer vs Editing Split (70/30 Rule)

**Viewer (automated):** sequencing + camera focus, subtitles, vote reveal, deaths, lighting,
role badges + selective reasoning.

**Editing (human):** cold open, commentary, music/SFX, cuts, zooms/slow-mo, memes, end analysis.

---

## Open Questions

- **Night Zero:** Skip in viewer, or show Mafia planning in omniscient?
- **Camera:** Scripted presets or dynamic "director"?
- **Subtitles:** Render in viewer or leave for editing?
- **Live mode:** Future streaming support needed?
- **Animation depth:** Simple idle or expressive reactions?

---

## References

- **Turing Games:** 3D Roblox-style, scene variety, selective reasoning
- **Neurotoster:** 2D circles, sequential voting, clean UI
- **Town of Salem:** Role iconography, death states
