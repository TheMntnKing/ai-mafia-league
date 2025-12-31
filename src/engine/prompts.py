"""Prompt templates and builders for ContextBuilder."""

from __future__ import annotations

RULES_SUMMARY = """You are playing Mafia with 7 players: 2 Mafia, 1 Detective, 4 Town.

ROLES:
- Town: No special abilities. Win by eliminating both Mafia.
- Detective: Town-aligned. Can investigate one player per night to learn if they are Mafia.
- Mafia: Know each other. Can kill one player per night. Win when Mafia >= Town-aligned.

GAME FLOW:
1. Day Phase: All players discuss, each nominates one player. Then vote.
   - Plurality vote eliminates a player. Skip wins mean no elimination. Player ties (or skip tied with one player) trigger revote.
2. Night Phase: Mafia choose a kill target. Detective investigates.
3. Game ends when all Mafia are dead (Town wins) or Mafia >= Town-aligned (Mafia wins).

RULES:
- Each speech should be ~50-100 words.
- Votes must be for a nominated player or "skip".
- Never reveal other players' hidden information you don't have."""

NIGHT_ZERO_PROMPT_FIRST = """[YOUR TASK: NIGHT ZERO COORDINATION]
This is Night Zero. No kill tonight - just coordination with your partner.

Share your initial strategy:
- Signals or code words to use during day discussion
- Cover stories if accused
- Initial suspicion targets to push on Town
- How you'll coordinate without being obvious

Provide your strategy in the 'speech' field. The 'nomination' field is not used tonight."""

NIGHT_ZERO_PROMPT_SECOND = """[YOUR TASK: NIGHT ZERO COORDINATION]
Your partner shared their strategy:
---
{partner_strategy}
---

Now share YOUR strategy. Discuss:
- Signals or code words to use during day discussion
- Cover stories if accused
- Initial suspicion targets to push on Town
- How you'll coordinate without being obvious

Provide your strategy in the 'speech' field. The 'nomination' field is not used tonight."""


def build_night_zero_prompt(partner_strategy: str | None) -> str:
    if partner_strategy:
        return NIGHT_ZERO_PROMPT_SECOND.format(partner_strategy=partner_strategy)
    return NIGHT_ZERO_PROMPT_FIRST


SPEAK_PROMPT_TEMPLATE = """[YOUR TASK: SPEAK]
It's your turn to speak in the discussion.

1. Observe what has happened and update your suspicions
2. Decide what information to share vs hide
3. Give a speech (~50-100 words) that fits your persona
4. You MUST nominate exactly one living player for potential elimination (or "skip" on Day 1)
5. If you nominate someone, clearly explain why (especially on Day 1)
{day_one_note}
Valid nomination targets: {nomination_targets}

 Fill out ALL fields in the schema (observations → suspicions → strategy → reasoning),
 then your actual speech and nomination."""

VOTE_PROMPT_TEMPLATE = """[YOUR TASK: VOTE]
Discussion is complete. Time to vote.

1. Review the discussion and your suspicions
2. Consider who is most likely Mafia
3. Vote for one nominated player, or "skip" if uncertain
{vote_day_one_note}
Valid vote options: {vote_options}

 Fill out ALL fields in the schema (observations → suspicions → strategy → reasoning),
 then provide your vote."""

NIGHT_KILL_PROMPT_TEMPLATE = """[YOUR TASK: MAFIA NIGHT KILL]
It's night. Choose a target to kill.

1. Consider who threatens your team (Detective suspects, strong Town leaders)
2. Coordinate with your partner's suggestion if provided
3. Provide a message to your partner explaining your reasoning
4. Choose a target or "skip" to spare everyone tonight

Valid targets: {living_except_self}

Fill out ALL fields in the schema (observations → suspicions → strategy → reasoning),
then provide your target."""

INVESTIGATION_PROMPT_TEMPLATE = """[YOUR TASK: DETECTIVE INVESTIGATION]
It's night. Choose someone to investigate.

1. Consider who is most suspicious
2. Think about how you'll use the information
3. Choose a target to learn if they are Mafia

Valid targets: {living_except_self}

 Fill out ALL fields in the schema (observations → suspicions → strategy → reasoning),
 then provide your target."""

LAST_WORDS_PROMPT_TEMPLATE = """[YOUR TASK: LAST WORDS]
You have been eliminated from the game. This is your final statement.

You may:
- Share your suspicions about who is Mafia
- Reveal your role if you wish
- Give advice to remaining players
- Say goodbye in your persona's style
{last_words_role_note}

 Keep it brief and impactful. Fill out all fields, including your reasoning,
 then provide your final message."""

DEFENSE_PROMPT = """[YOUR TASK: DEFENSE]
You are tied in the vote and must defend yourself.

1. Address the accusations against you
2. Make your case for why you should stay
3. Redirect suspicion if appropriate

 Give a brief but compelling defense speech in your persona's style.
 Fill out ALL fields in the schema, including your reasoning, then provide your defense."""


def build_speak_prompt(nomination_targets: str, day_one_note: str) -> str:
    return SPEAK_PROMPT_TEMPLATE.format(
        day_one_note=day_one_note,
        nomination_targets=nomination_targets,
    )


def build_vote_prompt(vote_options: str, vote_day_one_note: str) -> str:
    return VOTE_PROMPT_TEMPLATE.format(
        vote_day_one_note=vote_day_one_note,
        vote_options=vote_options,
    )


def build_night_kill_prompt(living_except_self: str) -> str:
    return NIGHT_KILL_PROMPT_TEMPLATE.format(living_except_self=living_except_self)


def build_investigation_prompt(living_except_self: str) -> str:
    return INVESTIGATION_PROMPT_TEMPLATE.format(living_except_self=living_except_self)


def build_last_words_prompt(last_words_role_note: str) -> str:
    return LAST_WORDS_PROMPT_TEMPLATE.format(
        last_words_role_note=last_words_role_note
    )
