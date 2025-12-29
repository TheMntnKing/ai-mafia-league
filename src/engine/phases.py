"""Game phase execution logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.voting import VoteResolver
from src.schemas import ActionType, DefenseSpeech, Event, PlayerMemory

if TYPE_CHECKING:
    from src.engine.events import EventLog
    from src.engine.state import GameStateManager
    from src.engine.transcript import TranscriptManager
    from src.players.agent import PlayerAgent


def _get_recent_events(
    event_log: EventLog,
    event_cursors: dict[str, int],
    player_name: str,
) -> list[Event]:
    """Return public events since the player's last turn and advance cursor."""
    start_index = event_cursors.get(player_name, 0)
    events = event_log.get_public_view(start_index)
    event_cursors[player_name] = len(event_log.events)
    return events


class NightZeroPhase:
    """
    Night Zero: Mafia coordination (no kill).

    Single round where Mafia players share initial strategy.
    """

    async def run(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        event_log: EventLog,
        event_cursors: dict[str, int],
    ) -> None:
        """Run Night Zero coordination."""
        event_log.add_phase_start("night_zero", 0)

        mafia_agents = [a for a in agents.values() if a.role == "mafia"]

        if len(mafia_agents) != 2:
            return

        # Each Mafia shares strategy
        strategies = {}
        for agent in mafia_agents:
            game_state = state.get_public_state()
            memory = PlayerMemory(facts={}, beliefs={})

            response = await agent.act(
                game_state,
                transcript=[],
                memory=memory,
                action_type=ActionType.SPEAK,
                recent_events=_get_recent_events(event_log, event_cursors, agent.name),
            )
            strategies[agent.name] = response.output.get("speech", "")


class DayPhase:
    """
    Day Phase: Discussion and voting.

    1. Announce death (if any)
    2. Discussion: each player speaks in order, nominates
    3. Voting: collect votes, resolve
    4. Revote if tied
    """

    def __init__(self):
        self.vote_resolver = VoteResolver()

    async def run(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        transcript_manager: TranscriptManager,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
        event_cursors: dict[str, int],
        night_kill: str | None = None,
        night_kill_last_words: str | None = None,
    ) -> tuple[str | None, dict[str, PlayerMemory]]:
        """
        Run day phase.

        Returns:
            (eliminated_player, updated_memories)
        """
        event_log.add_phase_start(state.phase, state.round_number)
        transcript_manager.start_round(
            state.round_number, night_kill, night_kill_last_words
        )

        # Discussion phase
        speaking_order = state.get_speaking_order()
        nominations: list[str] = []

        for speaker_name in speaking_order:
            agent = agents[speaker_name]
            game_state = state.get_public_state()
            game_state.nominated_players = nominations.copy()

            transcript = transcript_manager.get_transcript_for_player(state.round_number)

            response = await agent.act(
                game_state,
                transcript,
                memories[speaker_name],
                ActionType.SPEAK,
                recent_events=_get_recent_events(event_log, event_cursors, speaker_name),
            )

            memories[speaker_name] = response.updated_memory

            speech_text = response.output.get("speech", "")
            nomination = response.output.get("nomination", "")

            transcript_manager.add_speech(speaker_name, speech_text, nomination)
            event_log.add_speech(speaker_name, speech_text, nomination, response.output)

            if nomination and nomination not in nominations and state.is_alive(nomination):
                nominations.append(nomination)
                state.add_nomination(nomination)

        # Voting phase
        votes = {}
        for voter_name in speaking_order:
            agent = agents[voter_name]
            game_state = state.get_public_state()

            response = await agent.act(
                game_state,
                transcript_manager.get_transcript_for_player(
                    state.round_number, full=True
                ),
                memories[voter_name],
                ActionType.VOTE,
                recent_events=_get_recent_events(event_log, event_cursors, voter_name),
            )

            memories[voter_name] = response.updated_memory
            votes[voter_name] = response.output.get("vote", "skip")
            state.record_vote(voter_name, votes[voter_name])

        # Resolve vote
        result = self.vote_resolver.resolve(votes, len(speaking_order))
        eliminated = None
        defense_speeches: list[DefenseSpeech] | None = None
        revote: dict[str, str] | None = None
        revote_outcome: str | None = None

        if result.outcome == "eliminated":
            eliminated = result.eliminated
            last_words = await self._get_last_words(
                agents[eliminated],
                state,
                memories[eliminated],
                event_log,
                event_cursors,
            )
            event_log.add_vote(votes, f"eliminated:{eliminated}", eliminated)
            event_log.add_last_words(eliminated, last_words)
            state.kill_player(eliminated)

        elif result.outcome == "revote":
            # Run revote
            eliminated, defense_speeches, revote, revote_outcome = await self._run_revote(
                agents,
                state,
                transcript_manager,
                event_log,
                memories,
                event_cursors,
                result.tied_players or [],
                votes,
                result.vote_counts,
            )
            event_log.add_vote(votes, "revote", None)
            if eliminated:
                state.kill_player(eliminated)

        else:
            event_log.add_vote(votes, "no_elimination", None)

        # Finalize transcript
        vote_outcome = result.outcome
        if eliminated:
            vote_outcome = f"eliminated:{eliminated}"

        transcript_manager.finalize_round(
            round_number=state.round_number,
            night_kill=night_kill,
            last_words=night_kill_last_words,
            votes=votes,
            vote_outcome=vote_outcome,
            defense_speeches=defense_speeches,
            revote=revote,
            revote_outcome=revote_outcome,
        )

        return eliminated, memories

    async def _get_last_words(
        self,
        agent: PlayerAgent,
        state: GameStateManager,
        memory: PlayerMemory,
        event_log: EventLog,
        event_cursors: dict[str, int],
    ) -> str:
        """Get eliminated player's last words."""
        response = await agent.act(
            state.get_public_state(),
            [],
            memory,
            ActionType.LAST_WORDS,
            recent_events=_get_recent_events(event_log, event_cursors, agent.name),
        )
        return response.output.get("text", "")

    async def _run_revote(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        transcript_manager: TranscriptManager,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
        event_cursors: dict[str, int],
        tied_players: list[str],
        votes: dict[str, str],
        vote_counts: dict[str, int],
    ) -> tuple[str | None, list[DefenseSpeech], dict[str, str], str]:
        """Run revote with defenses."""
        defense_speeches: list[DefenseSpeech] = []
        defense_context = {
            "tied_players": tied_players,
            "votes": votes,
            "vote_counts": vote_counts,
        }

        # Defense speeches
        for name in tied_players:
            agent = agents[name]
            response = await agent.act(
                state.get_public_state(),
                transcript_manager.get_transcript_for_player(state.round_number),
                memories[name],
                ActionType.DEFENSE,
                recent_events=_get_recent_events(event_log, event_cursors, name),
                action_context={"defense_context": defense_context},
            )
            text = response.output.get("text", "")
            defense_speeches.append(DefenseSpeech(speaker=name, text=text))
            event_log.add_defense(name, text)

        # Revote
        revotes = {}
        speaking_order = state.get_speaking_order()
        for voter_name in speaking_order:
            agent = agents[voter_name]
            game_state = state.get_public_state()
            game_state.nominated_players = tied_players

            response = await agent.act(
                game_state,
                transcript_manager.get_transcript_for_player(
                    state.round_number, full=True
                ),
                memories[voter_name],
                ActionType.VOTE,
                recent_events=_get_recent_events(event_log, event_cursors, voter_name),
            )
            revotes[voter_name] = response.output.get("vote", "skip")

        result = self.vote_resolver.resolve_revote(
            revotes, len(speaking_order), tied_players
        )

        eliminated = None
        if result.outcome == "eliminated":
            eliminated = result.eliminated
            last_words = await self._get_last_words(
                agents[eliminated],
                state,
                memories[eliminated],
                event_log,
                event_cursors,
            )
            event_log.add_last_words(eliminated, last_words)

        revote_outcome = result.outcome
        if eliminated:
            revote_outcome = f"eliminated:{eliminated}"

        return eliminated, defense_speeches, revotes, revote_outcome


class NightPhase:
    """
    Night Phase: Mafia kill and Detective investigation.
    """

    async def run(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
        event_cursors: dict[str, int],
    ) -> tuple[str | None, str | None, dict[str, PlayerMemory]]:
        """
        Run night phase.

        Returns:
            (killed_player, last_words, updated_memories)
        """
        event_log.add_phase_start(state.phase, state.round_number)

        # Mafia coordination
        kill_target = await self._run_mafia_coordination(
            agents, state, event_log, memories, event_cursors
        )

        # Detective investigation
        await self._run_detective_investigation(
            agents, state, event_log, memories, event_cursors
        )

        # Execute kill and get last words
        last_words = None
        if kill_target and kill_target in agents:
            # Get last words before killing
            response = await agents[kill_target].act(
                state.get_public_state(),
                [],
                memories[kill_target],
                ActionType.LAST_WORDS,
                recent_events=_get_recent_events(event_log, event_cursors, kill_target),
            )
            last_words = response.output.get("text", "")
            event_log.add_last_words(kill_target, last_words)
            state.kill_player(kill_target)

        return kill_target, last_words, memories

    async def _run_mafia_coordination(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
        event_cursors: dict[str, int],
    ) -> str | None:
        """Run Mafia kill coordination (2-round protocol)."""
        mafia_agents = [
            a for a in agents.values()
            if a.role == "mafia" and state.is_alive(a.name)
        ]

        if not mafia_agents:
            return None

        if len(mafia_agents) == 1:
            # Single Mafia, direct choice
            agent = mafia_agents[0]
            game_state = state.get_public_state()
            # Filter out self from targets
            game_state.living_players = [
                p for p in game_state.living_players if p != agent.name
            ]

            response = await agent.act(
                game_state,
                [],
                memories[agent.name],
                ActionType.NIGHT_KILL,
                recent_events=_get_recent_events(event_log, event_cursors, agent.name),
            )
            memories[agent.name] = response.updated_memory
            target = response.output.get("target", "skip")

            event_log.add_night_kill(
                target if target != "skip" else None,
                response.output,
            )
            return target if target != "skip" else None

        # Round 1: Both propose
        proposals = {}
        for agent in mafia_agents:
            game_state = state.get_public_state()
            # Filter out self and partner
            game_state.living_players = [
                p for p in game_state.living_players
                if p != agent.name and p != agent.partner
            ]

            response = await agent.act(
                game_state,
                [],
                memories[agent.name],
                ActionType.NIGHT_KILL,
                recent_events=_get_recent_events(event_log, event_cursors, agent.name),
            )
            memories[agent.name] = response.updated_memory
            proposals[agent.name] = response.output.get("target", "skip")

        targets = list(proposals.values())

        # Check agreement
        if targets[0] == targets[1]:
            target = targets[0] if targets[0] != "skip" else None
            event_log.add_night_kill(target, {"proposals": proposals})
            return target

        if targets[0] == "skip" and targets[1] == "skip":
            event_log.add_night_kill(None, {"proposals": proposals})
            return None

        # Round 2: Try again with partner's proposal visible
        # (simplified: first Mafia by seat decides on disagreement)
        first_mafia = min(mafia_agents, key=lambda a: a.seat)
        target = proposals[first_mafia.name]
        target = target if target != "skip" else None

        event_log.add_night_kill(target, {"proposals": proposals, "decided_by": first_mafia.name})
        return target

    async def _run_detective_investigation(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
        event_cursors: dict[str, int],
    ) -> None:
        """Run Detective investigation."""
        detective_agents = [
            a for a in agents.values()
            if a.role == "detective" and state.is_alive(a.name)
        ]

        if not detective_agents:
            return

        agent = detective_agents[0]
        game_state = state.get_public_state()
        # Filter out self
        game_state.living_players = [
            p for p in game_state.living_players if p != agent.name
        ]

        response = await agent.act(
            game_state,
            [],
            memories[agent.name],
            ActionType.INVESTIGATION,
            recent_events=_get_recent_events(event_log, event_cursors, agent.name),
        )
        memories[agent.name] = response.updated_memory

        target = response.output.get("target", "")
        if target and target in state.players:
            is_mafia = state.get_player_role(target) == "mafia"
            result = "Mafia" if is_mafia else "Not Mafia"
            memory = memories[agent.name]
            facts = dict(memory.facts)
            results = list(facts.get("investigation_results", []))
            results.append({"target": target, "result": result})
            facts["investigation_results"] = results
            memories[agent.name] = PlayerMemory(
                facts=facts,
                beliefs=dict(memory.beliefs),
            )
            event_log.add_investigation(target, result, response.output)
