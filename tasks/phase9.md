# Phase 9: Roster + Role Expansion (Engine)

**Goal:** Expand the game engine to a 10-player roster with Doctor support and updated logs,
so the viewer can render full games.

**Status:** 🚧 IN PROGRESS

**Prerequisites:** Phase 1-8 complete

---

## Scope

- **Roster:** Expand default player count from 7 to 10.
- **Roles:** Add Doctor + extra Mafia (3 Mafia total).
- **Night flow:** Mafia kill → Doctor save → Detective investigate.
- **Logs:** Emit doctor protection events and state changes in replay logs.
- **Assets:** Define prompt pack for 10-player character roster (for GLB generation).

---

## Tasks

- [ ] Add Doctor role:
  - Night action: choose a player to protect
  - If protected target = Mafia kill target, cancel death
  - Log event for protection outcome
- [ ] Add 3 players to default roster (10 total)
- [ ] Add 3rd Mafia role (balance update)
- [ ] Update night resolution ordering and public/private log fields
- [ ] Update log schema + parser to include Doctor events
- [ ] Update tests for new roles and night flow
- [ ] Create 10-player character prompt pack (reference + style prompts)
- [ ] Generate a sample 10-player game log

---

**Deliverable:** 10-player games with Doctor role, updated logs, and a full roster prompt pack.
