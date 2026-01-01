# Phase 9: Replay Viewer (React + Vite)

> **STATUS: ARCHIVED**
>
> This phase has been superseded by Phase 10 (3D Voxel Viewer). The 2.5D CSS approach
> proved too static for YouTube content. We're starting fresh with React Three Fiber.
> See `tasks/phase10.md` and `docs/replay_vision.md` for the new direction.
>
> The code in `viewer/` will be cleaned up and rebuilt.

---

**Original Goal:** Transform the basic React viewer into the **2.5D Cinematic Stage** described in `docs/replay_vision.md`. The viewer will act as a visual "Director," interpreting the game log into a watchable, TV-style show.

---

## Scope

- **Core:** React + Vite app in `viewer/`.
- **Layout:** "Talk-Show" stage (semi-arc seating) with 2.5D depth.
- **Visuals:** "Digital Tabletop" aesthetic (circular character portraits, wood textures).
- **Logic:** Phase navigation, event stepping, public/omniscient modes.
- **UI:** Cinematic speech bubbles, vote tokens, and dynamic lighting.

---

## Viewer App Decisions

- **Location:** `viewer/` (separate frontend workspace).
- **Framework:** React + Vite (JavaScript).
- **Build output:** `viewer/dist` (build-only; do not commit).
- **Data Source:** File-drop JSON loading (no backend server required).
- **Architecture:** "Headless" state management (logic decoupled from the 2.5D renderer).
