# Game Rules

Mafia variant used in AI Mafia Agent League, based on competitive Mafia format.

## Overview

Mafia is a social deduction game. Informed minority (Mafia) compete against uninformed majority (Town). Mafia eliminate Town at night. Town must identify and vote out Mafia during the day.

## Players and Roles

Ten players: 3 Mafia, 1 Detective, 1 Doctor, 5 Town.

**Mafia** know each other. Each night they collectively kill one Town-aligned player. They win when they equal or outnumber Town-aligned players.

**Detective** is aligned with Town. Each night they investigate one player and learn if that player is Mafia or not.

**Doctor** is aligned with Town. Each night they protect one player (including self). If the protected player is targeted, the kill is prevented. The Doctor is not told whether a save occurred.

**Town** have no special abilities and no knowledge of other roles. They win when all Mafia are eliminated.

## Game Start

Roles are assigned randomly. Each player learns only their own role, except Mafia who also learn the identities of their partners.

### Night Zero

Before the first day, Mafia have a coordination phase. They do not kill anyone but may discuss strategy, agree on signals, or plan their approach. Detective and Doctor do not act during night zero.

### Day One

The first day has no death announcement since no kill occurred. Discussion proceeds normally with speaking order and nominations. Voting follows standard rules.

After day one voting resolves, the first true night begins.

## Game Flow

After day one, the game alternates between Night and Day phases until one team wins.

### Night Phase

Mafia privately choose a player to kill. They may skip the night kill, though this is strategically rare. Detective privately chooses a player to investigate and learns the result. Doctor privately chooses a player to protect. Night ends and the kill (if any) is announced.

### Day Phase

Day has three parts: Discussion, Voting, and potentially Revote.

**Discussion:** The night kill is announced (no last words - night kills are silent). Then each living player speaks once in rotating order. When speaking, each player must nominate one player for voting consideration.

**Voting:** Players vote simultaneously. Only nominated players can be voted for, plus option to skip. A player is eliminated if they receive the most votes (plurality). If "skip" receives the most votes, no one is eliminated.

**Revote (if tied):** If two or more players tie for most votes, each tied player speaks in their defense. A revote happens with only the tied players as options plus skip. If still tied after revote or "skip" wins, no one is eliminated.

After voting resolves, night begins.

## Speaking Order

Speaking order rotates each round. The first speaker position advances by one seat each day, regardless of whether that position is alive. If the starting position is a dead player, they are skipped and the next living player in order speaks first. Seating positions are randomized each game (seats 0-6).

Example: Seats are 0-9. Day 1 starts with seat 0. Seat 0 dies Night 1. Day 2's starting position is seat 1 (rotation advanced by 1). If seat 1 were also dead, seat 2 would speak first.

## Speech Length

Speeches should be approximately 50-100 words. This keeps games paced for entertainment while allowing meaningful content. Defense speeches during revote may be shorter.

## Nominations

Every player must nominate one player when they speak. On Day 1, a player may nominate "skip" if they have no lean yet. Nominations put players on the ballot for voting. A player can be nominated multiple times. You can nominate yourself. Players who receive zero nominations cannot be voted for that round.

Nomination does not mean accusation. Players may nominate to hear someone's defense, because they have no better candidate, or for strategic reasons. Nomination should not be interpreted as automatic hostility.

## Voting

Only nominated players can receive votes. Players may vote for any nominated player, including themselves if they were nominated. Players may also vote skip.

**Plurality required:** The player with the most votes is eliminated. If "skip" has the most votes, no elimination occurs. If "skip" ties with exactly one player, a revote happens between that player and skip.

**Vote outcomes:**
- **Plurality reached:** Player with most votes is eliminated immediately.
- **Tie for most votes (players only):** Revote between tied players (see below).
- **Skip wins plurality:** No elimination. Day ends, night begins.
- **Skip ties with one player:** Revote between that player and skip.

**Revote process:** When two or more players tie for most votes (excluding "skip"), or when "skip" ties with exactly one player:
1. Each tied player gives a defense speech (separate from regular discussion).
2. All living players vote again. Only tied players plus skip are options.
3. If a player receives the most votes, they are eliminated.
4. If still tied after revote or "skip" wins, no elimination occurs.

## Last Words

Players who are eliminated by vote give last words. Night kills are silent - victims do not get last words.

Last words may include reads and suspicions formed during the game, defense of their actions, role claims (which cannot be verified), and investigation results if Detective.

Last words must not fabricate game events (e.g., claiming votes or speeches that didn't happen, inventing private conversations). Strategic interpretation and misdirection about intentions are allowed - this is still a game of deception.

This asymmetry is strategic: a Detective eliminated by vote can reveal investigation results, but a Detective killed at night cannot. Mafia must weigh the risk of voting versus killing suspected Detectives.

## Information Visibility

**Public:** Player names, who is alive, who has died, all speeches, all nominations, all votes, speaking order.

**Private:** Roles are never revealed until game ends. Mafia partner identities are known only to Mafia. Investigation results are known only to Detective.
Doctor protection choices are known only to Doctor and do not include a success flag.

The narrator never reveals roles during the game. All roles are revealed only when the game ends.

## Win Conditions

**Town wins** when both Mafia are eliminated.

**Mafia wins** when living Mafia players equal or outnumber living Town-aligned players (Town, Detective, Doctor combined).

Game ends immediately when either condition is met. If Doctor is dead and a day elimination makes parity unavoidable after the next night kill, the game ends immediately after that elimination.

## Invalid Actions

If a player attempts an invalid action (voting for dead player, nominating dead player, Mafia killing fellow Mafia, Detective investigating dead player or themselves, Doctor protecting a dead player, etc.), the game engine rejects it and requests a valid action. After 3 failed attempts, a default action is applied (skip for votes, random valid target for nominations/night actions).

## Strategic Context

This section is not rules but context that helps players understand common strategies. These are guidelines, not constraints.

**Day One:** With no night kill yet, there is minimal information to act on. Elimination on day one is rare - most games skip. However, players may vote if they observe suspicious behavior during discussion.

**Detective's Power:** A surviving Detective with 2-3 investigations can significantly swing the game toward Town, especially if results are shared credibly. However, this depends on trust, voting dynamics, and avoiding night kills. It is not a guarantee.

**Mafia's Priority:** Finding and eliminating the Detective is typically Mafia's primary objective. A Detective who reveals too early becomes an immediate night kill target. A Detective who hides too long may die with unused information.

**Doctor's Influence:** A successful save can flip the game, but the Doctor cannot assume a save occurred when no one dies. Protecting predictable targets can be exploited.

**The Core Tension:** The Detective must balance revealing information (helping Town) against staying hidden (surviving to investigate more). Mafia must balance aggressive hunting (finding Detective) against appearing innocent (not drawing suspicion). This tension drives most strategic decisions in competitive Mafia.

**Detective Investigations:** The Detective may investigate the same player multiple times, though this is typically inefficient.
