# Phase 11: Production Readiness

**Goal:** Transform the functional viewer (Phase 10) into YouTube-ready content production tool.

**Status:** ❌ NOT STARTED

**Prerequisites:** Phase 10 complete (10.0-10.6)

**Scope:** Audio integration, export workflow, advanced animation, UI polish, accessibility

---

## Overview

Phase 10 delivers a **functional viewer** (60-70% ready) for internal testing and debugging.

Phase 11 bridges the gap to the **70/30 rule** from `docs/replay_vision.md`:
- Viewer produces 70% watchable content out of the box
- Editing adds the final 30% (music, commentary, cuts, memes)

---

## Phases

### Phase 11.1: Audio & Environment

**Goal:** Integrate TTS audio and polish scene atmosphere.

**Tasks:**
- [ ] TTS audio integration:
  - Load audio files from log metadata or file paths (e.g., `event.data.audio_url` or `logs/audio/{game_id}/{event_id}.mp3`)
  - Sync audio playback with event timing
  - Audio controls (volume, mute)
  - Playback speed controls (0.5x, 1x, 2x) with pitch preservation
  - Preload audio to prevent stuttering
  - Handle missing audio gracefully (fallback to subtitles-only mode)
- [ ] Scene environment detail:
  - Add fog to Mafia lair (R3F `<Fog>` or particle system)
  - Add detective desk lamp (point light + emissive mesh for `#FFC857` accent)
  - Add town square props:
    - Houses (low-poly buildings in background)
    - Street lamps (warm glow at night)
    - Benches or barrels (foreground detail)
- [ ] Font loading fix:
  - Add Space Grotesk to `viewer/index.html` from Google Fonts
  - Weights: 400 (regular), 700 (bold)

**Deliverable:** Audio plays synchronized with events. Scenes feel atmospheric. Typography correct.

**Viewer Readiness:** ~80% - Ready for screen recording, rough but watchable

---

### Phase 11.2: Export & Production

**Goal:** Prepare viewer output for editing workflow.

**Tasks:**
- [ ] Export timeline as JSON:
  - Timestamps for each event (relative to game start)
  - Speaker names and roles
  - Event types (speech, vote, elimination, night_kill, investigation, etc.)
  - Key moments (betrayals, eliminations, role reveals)
  - Export button in UI (downloads `{game_id}_timeline.json`)
- [ ] Export cut points:
  - Day/night transitions
  - Major events (eliminations, night kills announced)
  - Featured reasoning moments (when implemented in 10.6)
  - Format: array of `{timestamp, label, type}` for editing software markers
- [ ] Recording integration:
  - Document screen recording workflow:
    - OBS Studio setup (capture browser window, 1080p60)
    - Loom integration (if applicable)
    - Chrome tab capture (for quick tests)
  - Optional: frame-by-frame export (viewer renders to canvas, exports PNG sequence)
- [ ] Metadata export:
  - Game summary: winner, final living/dead counts, game duration
  - Role reveal timeline: when each role is revealed (death, game end)
  - Vote history: all votes with timestamps
  - Casualty list: who died when, how (night kill vs vote)

**Deliverable:** Editor can easily extract footage and metadata for post-production.

**Viewer Readiness:** ~90% - Full production pipeline complete

---

### Phase 11.3: Animation & Expression

**Goal:** Characters feel expressive and reactive.

**Tasks:**
- [ ] Eye state system:
  - Eye geometry with swappable shapes (neutral, surprised, suspicious, skeptical)
  - Dead state (X eyes) already implemented in Phase 10 ✅
  - Eye shape changes based on game events:
    - Surprised when nominated
    - Skeptical during defense speeches
    - Neutral default
  - Smooth transitions with React Spring
- [ ] Gesture animations:
  - Point at nomination target (arm raise, point gesture)
  - Defensive stance during defense speech (hands up, lean back)
  - Relieved pose when vote count doesn't reach elimination (slump, exhale)
  - Implement via simple bone rotations or mesh deformations
- [ ] Reaction system:
  - Shock when nominated (eyes widen, body jolt)
  - Relief when vote passes without elimination (relax pose)
  - Optional: head turns toward speaker when mentioned
  - Reactions should be subtle and quick (0.5-1 second)
- [ ] Idle variation:
  - Bobbing animation (planned in Phase 10.4) ✅
  - Occasional subtle head movement (look left/right, nod)
  - Breathing animation (chest rise/fall) - optional for polish
  - Randomize timing to avoid synchronized movement

**Deliverable:** Characters react to game events with simple, expressive animations.

**Viewer Readiness:** ~95% - Premium feel, minimal editing needed

---

### Phase 11.4: Polish & Accessibility

**Goal:** Production-ready UX with polish and accessibility.

**Tasks:**
- [ ] Game summary view:
  - Winner announcement with confetti or victory animation
  - Casualty list (deaths in chronological order)
  - Key betrayals timeline (who lied to who, successful Mafia plays)
  - MVP (Most Valuable Player) highlights:
    - Best lie (Mafia)
    - Best deduction (Detective or Villager)
    - Most votes received (chaos agent)
- [ ] Player scoreboard:
  - Living/dead status (real-time)
  - Roles revealed (omniscient mode, or after game end in public mode)
  - Nomination history (who nominated who)
  - Vote history (who voted for who)
  - Compact panel, toggleable visibility
- [ ] UI enhancements:
  - Event filtering:
    - Show only eliminations
    - Show only speeches
    - Show only votes
    - Show only night events (omniscient mode)
  - Jump to day/night buttons (quick navigation)
  - Full-screen mode (hide UI chrome, focus on 3D scene)
  - Progress indicator (current event / total events, visual timeline)
- [ ] Accessibility:
  - Keyboard navigation:
    - Tab through UI elements
    - Arrow keys for prev/next event
    - Space for play/pause
    - Number keys for speed (1 = 1x, 2 = 2x, etc.)
  - Screen reader support:
    - ARIA labels for all buttons
    - Event announcements (e.g., "Alice nominates Bob")
  - Colorblind mode:
    - Adjust role colors for protanopia (red-green colorblind)
    - Adjust role colors for deuteranopia (red-green colorblind)
    - Use patterns or icons in addition to color
  - High contrast mode (increase contrast for low-vision users)
- [ ] Performance optimization:
  - LOD (Level of Detail) for character models:
    - High LOD when camera is close
    - Low LOD when camera is far
  - Frustum culling (don't render off-screen characters)
  - Memory profiling:
    - Identify memory leaks (if any)
    - Optimize texture sizes
    - Dispose of unused geometries/materials
  - Target: 60fps at 1080p on mid-range hardware

**Deliverable:** Viewer is polished, accessible, and production-ready for YouTube content.

**Viewer Readiness:** 100% - Ship it to YouTube

---

## Success Criteria

Phase 11 complete when:

1. ✅ All Phase 10 criteria met
2. ✅ TTS audio plays synchronized with events
3. ✅ Audio controls (volume, mute, speed)
4. ✅ Atmospheric scenes (fog, props, lighting details)
5. ✅ Font rendering correct (Space Grotesk loaded)
6. ✅ Timeline export (JSON with timestamps, speakers, events)
7. ✅ Cut points export (key moments for editing)
8. ✅ Metadata export (game summary, role reveals, vote history)
9. ✅ Recording workflow documented
10. ✅ Eye expressions (neutral, surprised, suspicious)
11. ✅ Gesture animations (point, defensive stance, relief)
12. ✅ Reaction system (shock, relief, head turns)
13. ✅ Idle variation (bobbing, head movement, breathing)
14. ✅ Game summary view (winner, casualties, MVP)
15. ✅ Player scoreboard (status, roles, vote history)
16. ✅ UI enhancements (filtering, jump buttons, full-screen)
17. ✅ Accessibility (keyboard nav, screen reader, colorblind mode)
18. ✅ Performance optimized (60fps at 1080p)

---

## Integration with Editing Workflow (70/30 Rule)

### Viewer Provides (70%)
- Event sequencing (correct order)
- Character states (alive/dead, spotlight)
- Speech bubbles (text with TTS sync)
- Vote tokens (sequential reveal)
- Day/night atmosphere (scene + lighting)
- Reasoning panel (private thoughts in omniscient mode)
- Role badges (who is what)
- Camera presets (wide, speaker, vote tension)
- Timeline + metadata export

### Editing Adds (30%)
- Cold open hook (10-second betrayal/twist teaser)
- Character intros ("Meet the players" segment)
- Music/SFX (tension building, stingers)
- Commentary voiceover (strategic analysis, "watch this...")
- Boring part cuts (skip uneventful Day 1)
- Zoom/slow-mo (emphasize betrayal moments)
- End analysis ("Here's where Town lost...")
- Meme inserts (reaction images for virality)

---

## Open Questions

- **Live mode:** Do we need WebSocket support for streaming live games? (Future Phase 12?)
- **Multiplayer replays:** Should the viewer support side-by-side comparison of two games?
- **Mobile support:** Should the viewer work on mobile browsers, or desktop-only?
- **VR mode:** Is VR viewing ever needed? (Probably not for YouTube content)

---

## Testing

After each phase:

1. Load sample log from `logs/`
2. Verify new features work (audio, export, animations, etc.)
3. Test accessibility features (keyboard nav, colorblind mode)
4. Profile performance (60fps target)
5. Record a full game playback and export metadata
6. Edit exported footage in video editor (test workflow)

---

## File Structure

```
viewer/
├── src/
│   ├── components/
│   │   ├── AudioPlayer.jsx         # NEW: 11.1
│   │   ├── ExportPanel.jsx         # NEW: 11.2
│   │   ├── GameSummary.jsx         # NEW: 11.4
│   │   └── Scoreboard.jsx          # NEW: 11.4
│   ├── hooks/
│   │   ├── useAudioSync.js         # NEW: 11.1
│   │   ├── useExport.js            # NEW: 11.2
│   │   ├── useAnimations.js        # NEW: 11.3
│   │   └── useAccessibility.js     # NEW: 11.4
│   └── utils/
│       ├── audioLoader.js          # NEW: 11.1
│       ├── exportTimeline.js       # NEW: 11.2
│       └── performanceMonitor.js   # NEW: 11.4
```

---

## Dependencies

New dependencies for Phase 11:

```bash
cd viewer
npm install tone  # For audio playback with speed control
npm install file-saver  # For exporting JSON files
```

Optional:
```bash
npm install @react-three/postprocessing  # For visual effects (fog, glow)
npm install leva  # For debug controls (already in Phase 10)
```

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| 11.1 | Audio + environment | 3-5 days |
| 11.2 | Export + workflow | 2-3 days |
| 11.3 | Animation + expression | 4-6 days |
| 11.4 | Polish + accessibility | 3-5 days |
| **Total** | | **12-19 days** |

Assumes 1 developer, full-time work, with existing Phase 10 foundation.

---

## Next Steps

1. Complete Phase 10.6 (reasoning display)
2. Review Phase 11.1 tasks with team
3. Set up audio file structure in logs (e.g., `logs/audio/{game_id}/`)
4. Test TTS audio generation pipeline (ensure engine outputs audio files)
5. Begin Phase 11.1 implementation
