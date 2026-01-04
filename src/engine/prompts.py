"""Prompt templates and builders for ContextBuilder."""

from __future__ import annotations

RULES_SUMMARY = """You are playing Mafia with 10 players: 3 Mafia, 1 Detective, 1 Doctor, 5 Town.

WIN CONDITIONS:
- Town wins when all Mafia are eliminated.
- Mafia wins at parity (Mafia >= Town-aligned).

ROLES (known to all players):
- Town: No special abilities.
- Detective: Investigate one player per night to learn if they are Mafia.
- Doctor: Protect one player per night (can self).
- Mafia: Know each other. Choose one kill target per night.

DAY VOTE:
- Each living player nominates one living player (Day 1 may be "skip").
- Votes must be for a nominated player or "skip".
- Plurality vote eliminates a player; skip can win (no elimination).
- Ties among players (or skip tied with one player) trigger a revote.

NIGHT:
- Night Zero is coordination only (no kill).
- Mafia coordinate and choose a kill target.
- Doctor protects one player (can self).
- Detective investigates one player.

INTEGRITY:
- You may bluff about your role or investigation results as part of deception.
- Do not fabricate public events (votes, speeches, deaths) or claim access to private channels
- or actions you could not plausibly have (partner chat, other players' night actions).
- Stay in character."""

SGR_FIELD_GUIDE = (
    "Schema guidance: observations = public facts from this phase only; "
    "suspicions = persistent suspects + brief reasons (update, don’t reset); "
    "strategy = your ongoing plan/tactics for next actions (update, don’t reset); "
    "reasoning = 40-80 words (~2-4 sentences) internal monologue for replay, not a "
    "rewrite of your public speech. speech/nomination/vote/message/target = your action output."
)
SHORT_FIELD_GUIDE = (
    "Schema guidance: reasoning = private thoughts (40-80 words / ~2-4 sentences); "
    "text = what you say out loud."
)

ROLE_PLAYBOOKS: dict[str, list[str]] = {
    "town": [
        "Consider one main suspect + one backup + what would change your mind.",
        "If you speak early, consider nominating who you want to hear defend; if late, consider a viable vote target.",
        "Consider asking one pointed question to a slippery player.",
        "If the room is scattered, consider nudging convergence on 1–2 options.",
        "Avoid defaulting to quiet players; pull them in with a direct question.",
    ],
    "mafia": [
        "Aim to sound reasonable while nudging nominations/votes toward Town targets.",
        "If speaking early, consider a believable target with a simple, repeatable story.",
        "Keep your case short and consistent.",
        "If Town is split, consider keeping it split rather than unifying them.",
        "If a partner is doomed, mild distancing can help you survive.",
        "Consider a strategic role bluff if it flips a vote or protects partners.",
        "Night kills often target organizers or trust builders.",
    ],
    "detective": [
        "Consider revealing only when it changes today’s vote or you expect to die soon.",
        "If you find Mafia, consider nominating them so they’re vote-eligible.",
        "If you find “not Mafia” on a popular suspect, consider defending without instant claim.",
        "If you are in defense speech, consider hard-claiming with a clean results list.",
        "Prioritize checking influential players.",
        "When claiming, consider listing checks in order (Night X: target = result).",
    ],
    "doctor": [
        "Consider protecting likely night targets (leaders, claimed Detective).",
        "Consider rotating protections to avoid predictability.",
        "Consider self-protecting if under heavy suspicion.",
        "Consider protecting whoever matters most tomorrow, not today’s vote target.",
        "Watch for precise/hidden-info behavior as possible Detective.",
    ],
}


def build_role_playbook(role: str) -> str | None:
    lines = ROLE_PLAYBOOKS.get(role)
    if not lines:
        return None
    bullets = "\n".join(f"- {line}" for line in lines)
    return f"[ROLE PLAYBOOK]\n{bullets}"

NIGHT_ZERO_PROMPT_FIRST = """[YOUR TASK: NIGHT ZERO COORDINATION]
This is Night Zero. No kill tonight - just coordination with your partners.

Share your initial strategy:
- Signals or code words to use during day discussion
- Cover stories if accused
- Initial suspicion targets to push on Town
- How you'll coordinate without being obvious

Provide your strategy in the 'speech' field (~60-100 words). The 'nomination' field is not used tonight."""

NIGHT_ZERO_PROMPT_WITH_PARTNERS = """[YOUR TASK: NIGHT ZERO COORDINATION]
Your partners shared their strategies:
---
{partner_strategies}
---

Now share YOUR strategy. Discuss:
- Signals or code words to use during day discussion
- Cover stories if accused
- Initial suspicion targets to push on Town
- How you'll coordinate without being obvious

Provide your strategy in the 'speech' field (~60-100 words). The 'nomination' field is not used tonight."""


def build_night_zero_prompt(partner_strategies: dict[str, str] | None) -> str:
    if partner_strategies:
        lines = [
            f"- {name}: {strategy}"
            for name, strategy in partner_strategies.items()
            if strategy
        ]
        if not lines:
            lines = ["- (no partner strategies yet)"]
        return NIGHT_ZERO_PROMPT_WITH_PARTNERS.format(
            partner_strategies="\n".join(lines)
        )
    return NIGHT_ZERO_PROMPT_FIRST


SPEAK_PROMPT_TEMPLATE = """[YOUR TASK: SPEAK]
It's your turn to speak in the discussion.

1. Observe what has happened and update your suspicions
2. Decide what information to share vs hide
3. Give a speech (~80-140 words) that fits your persona
4. You MUST nominate exactly one living player for potential elimination (or "skip" on Day 1)
5. If you nominate someone, clearly explain why (especially on Day 1)
6. If information is thin, ask pointed questions and avoid overconfident claims
{day_one_note}
Valid nomination targets: {nomination_targets}

{sgr_field_guide}
Fill out ALL fields in the schema, then provide your speech and nomination."""

VOTE_PROMPT_TEMPLATE = """[YOUR TASK: VOTE]
Discussion is complete. Time to vote.

1. Review the discussion and your suspicions
2. Consider who is most likely Mafia
3. Vote for one nominated player, or "skip" if uncertain
4. Do not vote solely based on a nomination; weigh behavior and consistency
{vote_day_one_note}
Valid vote options: {vote_options}

{sgr_field_guide}
Fill out ALL fields in the schema, then provide your vote."""

NIGHT_KILL_PROMPT_TEMPLATE = """[YOUR TASK: MAFIA NIGHT KILL]
It's night. Choose a target to kill.

1. Consider who threatens your team (Detective suspects, strong Town leaders)
2. Coordinate with your partners' suggestions if provided
3. Provide a message to your partners explaining your reasoning (40-80 words / ~2-4 sentences)
4. Choose a target or "skip" to spare everyone tonight
Note: The "message" field is private to Mafia partners. Do not write public-facing speech.

Valid targets: {living_except_self}

{sgr_field_guide}
Fill out ALL fields in the schema, then provide your target."""

INVESTIGATION_PROMPT_TEMPLATE = """[YOUR TASK: DETECTIVE INVESTIGATION]
It's night. Choose someone to investigate.

1. Consider who is most suspicious
2. Think about how you'll use the information
3. Choose a target to learn if they are Mafia

Valid targets: {living_except_self}

{sgr_field_guide}
Fill out ALL fields in the schema, then provide your target."""

DOCTOR_PROTECT_PROMPT_TEMPLATE = """[YOUR TASK: DOCTOR PROTECTION]
It's night. Choose someone to protect.

1. Consider who is most likely to be targeted
2. Decide whether to protect yourself or another player
3. Choose one living player to protect

Valid targets: {living_players}

{sgr_field_guide}
Fill out ALL fields in the schema, then provide your target."""

LAST_WORDS_PROMPT_TEMPLATE = """[YOUR TASK: LAST WORDS]
You have been eliminated from the game. This is your final statement.

You may:
- Share your suspicions about who is Mafia
- Reveal your role if you wish
- Give advice to remaining players
- Say goodbye in your persona's style
If you are told this ends the game, you can drop pretense and speak freely.
{last_words_role_note}

Keep it brief (~60-100 words) and impactful.
{short_field_guide}
Fill out all fields, then provide your final message."""

DEFENSE_PROMPT = f"""[YOUR TASK: DEFENSE]
You are tied in the vote and must defend yourself.

1. Address the accusations against you
2. Make your case for why you should stay
3. Redirect suspicion if appropriate

Give a brief but compelling defense speech in your persona's style (~60-100 words).
{SHORT_FIELD_GUIDE}
Fill out all fields, then provide your defense."""


def build_speak_prompt(nomination_targets: str, day_one_note: str) -> str:
    return SPEAK_PROMPT_TEMPLATE.format(
        day_one_note=day_one_note,
        nomination_targets=nomination_targets,
        sgr_field_guide=SGR_FIELD_GUIDE,
    )


def build_vote_prompt(vote_options: str, vote_day_one_note: str) -> str:
    return VOTE_PROMPT_TEMPLATE.format(
        vote_day_one_note=vote_day_one_note,
        vote_options=vote_options,
        sgr_field_guide=SGR_FIELD_GUIDE,
    )


def build_night_kill_prompt(living_except_self: str) -> str:
    return NIGHT_KILL_PROMPT_TEMPLATE.format(
        living_except_self=living_except_self,
        sgr_field_guide=SGR_FIELD_GUIDE,
    )


def build_investigation_prompt(living_except_self: str) -> str:
    return INVESTIGATION_PROMPT_TEMPLATE.format(
        living_except_self=living_except_self,
        sgr_field_guide=SGR_FIELD_GUIDE,
    )


def build_doctor_protect_prompt(living_players: str) -> str:
    return DOCTOR_PROTECT_PROMPT_TEMPLATE.format(
        living_players=living_players,
        sgr_field_guide=SGR_FIELD_GUIDE,
    )


def build_last_words_prompt(last_words_role_note: str) -> str:
    return LAST_WORDS_PROMPT_TEMPLATE.format(
        last_words_role_note=last_words_role_note,
        short_field_guide=SHORT_FIELD_GUIDE,
    )
