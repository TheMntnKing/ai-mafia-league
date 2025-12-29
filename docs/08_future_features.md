# Future Features

Not in MVP scope but documented for later implementation.

## Tournament Format

Multi-game series (10-15 games) with fixed roster of personas.

**Features:**
- Cumulative memory: agents remember how each persona played in previous games
- Scoring system across games
- Personas can reference past behavior ("Last game you accused me wrongly...")

### Tournament Persistence (Persona Memory)

In tournaments, personas accumulate memory of opponents across games.

**What's remembered (post-game, all roles revealed):**
- Role history and outcomes
- Behavioral patterns per role (how they play as Town vs Mafia vs Detective)
- Relationship history (accusations, defenses, betrayals, alliances)
- Notable moments (memorable plays, lies caught, clutch saves)

**Format:** Free-form text summary per opponent, updated after each game. ~100-200 words per opponent.

**Cold start:** Game 1 has no tournament memory; only fixed lore applies.

**Factual guardrail:** Memories must only reference events in the engine summary + revealed roles (no invented events).

**Constraint:** Memory can inform suspicion but never proves the current role. Valid: "Viktor betrayed his partner last time he was Mafia" or "Viktor tends to be aggressive when Mafia." Invalid: "Viktor is Mafia this game because he did X last time." The memory informs how to READ behavior, not what role they have this game.

**Post-Game Reflection (7 LLM calls per game):**

Each agent generates their tournament memory updates in their own voice.

Input:
- Their persona (so reflection matches their voice/priorities)
- Revealed roles (the new information)
- Engine-extracted game summary (structured, no LLM needed)
- Their final belief state from the game
- Previous tournament memories of each opponent

Output:
- Updated memory per opponent (~50-100 words each, in persona voice)

**Storage:** Tournament memory keyed by (tournament_id, persona_id, opponent_id).

**At game start:** Inject roster-filtered opponent memories into context alongside fixed lore relationships.

**During game:** Tournament memory is read-only. In-game beliefs are tracked separately in per-game memory state.

---

## Post-Game Trash Talk

After each game ends and roles are revealed, players engage in free-form discussion. Pure entertainment feature - no structure, no voting.

**Purpose:** Boost engagement, create memorable content, let personas express personality.

**Behavior varies by persona:**
- Analytical: post-mortem analysis, calls out logical errors
- Salty: blames teammates, accuses others of luck
- Gracious: congratulates good plays, admits mistakes
- Troll: maximum salt, targets whoever killed them
- Cryptic: mysterious observations, no clear emotion

**Format:** ~10 messages total, reactive conversation flow.

**Speaker selection:**
1. First speaker: random
2. Next speaker: if previous message addressed someone (@name or clear reference), that persona gets first right of reply
3. Otherwise: choose from personas who haven't spoken recently (least-recently-spoken priority, random tie-break)
4. End after ~10 messages or natural conclusion

**Input per message:**
- Persona (including post-game style/tone)
- Revealed roles
- Engine-extracted game summary (key events to reference)
- Game outcome (winner, final state)
- Their belief state (what they THOUGHT vs reality - creates "I KNEW IT" moments)
- Previous trash talk messages (full conversation so far)

**Output:** Free-form message (~50-100 words), optionally addressing specific player(s).

**Example:**
```
[GAME ENDS - Mafia wins]

Viktor Cross: "Incredible. I built a perfect case against Tralalero on Day 2
and you all voted for ME. The evidence was right there. Elena, you had one job."

Tralalero: "The sea takes what the sea wants, my friend. Viktor, your case
was beautiful. But beauty drowns. Tralalero Tralala~ 🦈"

Elena Vance: "To be fair, Viktor, you WERE aggressive. That's literally
your Mafia tell. I played the odds."

Viktor Cross: "MY TELL? I'm aggressive when I'm RIGHT. Check the transcript!"
```

**Persona addition:** Consider adding `post_game_style` to persona's `voice_and_behavior` to guide trash talk tone.

---

## Additional Roles

Expand beyond base 7-player setup:

**Don (Mafia):** Appears innocent to Detective investigation. Adds deception layer.

**Doctor (Town):** Each night, chooses one player to protect from night kill. Cannot protect self (or can only protect self once). Adds protection/prediction dynamic.

**Role balance considerations:** More roles = more complexity. Test base game thoroughly first.

---

## Competition Platform

Open submissions for persona strategies.

**Format:**
- Same base model for all agents
- Competitors submit persona definitions (identity, voice_and_behavior, role_guidance)
- Ranked ladder based on win rate across many games
- Seasonal tournaments

**Fairness:** All personas use identical SGR schema, engine, and rules. Skill is in persona craft.

---

## Live Streaming

Real-time game execution with commentary for Twitch/YouTube.

**Challenges:**
- Pacing: LLM calls take time, need to fill gaps
- Presentation: How to show private reasoning without spoiling
- Interaction: Can viewers influence anything?

**Options:**
- Pre-recorded with editing (easier, better pacing)
- Live with human commentator filling gaps
- Live with AI narrator providing real-time commentary

---

## Visual Game Client

2D/3D game visualization for content production.

**Features:**
- Character sprites or 3D models for each persona
- AI-generated or recorded voiceover for speeches
- Animations for accusations, votes, deaths
- Visual representation of suspicion/trust levels

**Tiers:**
- Testing: Simple 2D visualization, basic animations
- Content: Full 3D with production quality, voice acting

---

## Narrator System

LLM-powered narrator for flavor and entertainment.

**Responsibilities:**
- Opening game introduction
- Night kill announcements with dramatic flair
- Vote result commentary
- Key moment highlights
- Game end summary

**Constraint:** Narrator NEVER paraphrases player speeches. Players receive exact transcripts. Narrator adds flavor around events, not interpretation of player intent.

**Implementation:** Optional for MVP. Can run games without narrator.

---

## Evaluation Framework

Beyond win rate - measuring game quality.

**Possible metrics:**
- Dramatic tension: Close votes, lead changes
- Deception success: How often Mafia avoided suspicion
- Surprise reveals: Gap between beliefs and revealed roles
- Entertainment value: Human ratings of game watchability

**Testing strategy:**
- Collect manual evaluation sets from game simulations
- Component-level evals based on game history
- A/B test persona variations
