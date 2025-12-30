"""Game phase execution logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.voting import VoteResolver
from src.schemas import ActionType, DefenseSpeech, PlayerMemory, Transcript

if TYPE_CHECKING:
    from src.engine.events import EventLog
    from src.engine.state import GameStateManager
    from src.engine.transcript import TranscriptManager
    from src.players.agent import PlayerAgent



class NightZeroPhase:
    """
    Night Zero: Mafia coordination (no kill).

    Sequential coordination where Mafia players share strategy.
    Second Mafia sees first Mafia's strategy before responding.
    Both strategies stored in both Mafia's memories for future reference.
    """

    async def run(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
    ) -> dict[str, PlayerMemory]:
        """
        Run Night Zero coordination.

        Returns:
            Updated memories dict with Mafia strategies stored
        """
        event_log.add_phase_start(
            "night_zero",
            0,
            stage="phase_start",
            state_public=state.get_public_snapshot(),
        )

        mafia_agents = [a for a in agents.values() if a.role == "mafia"]

        if len(mafia_agents) != 2:
            return memories

        # Sort by seat so coordination order is deterministic
        mafia_agents.sort(key=lambda a: a.seat)
        first_mafia, second_mafia = mafia_agents

        # First Mafia shares strategy
        game_state = state.get_public_state()
        response1 = await first_mafia.act(
            game_state,
            transcript=[],
            memory=memories[first_mafia.name],
            action_type=ActionType.SPEAK,
            action_context={"night_zero": True},
        )
        memories[first_mafia.name] = response1.updated_memory
        first_strategy = response1.output.get("speech", "")
        event_log.add(
            "night_zero_strategy",
            {
                "speaker": first_mafia.name,
                "text": first_strategy,
                "reasoning": response1.output,
            },
            private_fields=[
                "speaker",
                "text",
                "reasoning",
                "phase",
                "round_number",
                "stage",
                "state_public",
                "state_before",
                "state_after",
            ],
            phase=state.phase,
            round_number=state.round_number,
            stage="night_zero",
            state_public=state.get_public_snapshot(),
        )

        # Second Mafia sees first's strategy and responds
        response2 = await second_mafia.act(
            game_state,
            transcript=[],
            memory=memories[second_mafia.name],
            action_type=ActionType.SPEAK,
            action_context={
                "night_zero": True,
                "partner_strategy": first_strategy,
            },
        )
        memories[second_mafia.name] = response2.updated_memory
        second_strategy = response2.output.get("speech", "")
        event_log.add(
            "night_zero_strategy",
            {
                "speaker": second_mafia.name,
                "text": second_strategy,
                "reasoning": response2.output,
            },
            private_fields=[
                "speaker",
                "text",
                "reasoning",
                "phase",
                "round_number",
                "stage",
                "state_public",
                "state_before",
                "state_after",
            ],
            phase=state.phase,
            round_number=state.round_number,
            stage="night_zero",
            state_public=state.get_public_snapshot(),
        )

        # Store both strategies in both Mafia's memories for future reference
        for agent in mafia_agents:
            memory = memories[agent.name]
            facts = dict(memory.facts)
            facts["night_zero_strategies"] = {
                first_mafia.name: first_strategy,
                second_mafia.name: second_strategy,
            }
            memories[agent.name] = PlayerMemory(facts=facts, beliefs=dict(memory.beliefs))

        return memories


class DayPhase:
    """
    Day Phase: Discussion and voting.

    1. Announce death (if any) - no last words for night kills
    2. Discussion: each player speaks in order, nominates
    3. Voting: collect votes, resolve
    4. Revote if tied
    5. Last words only for day eliminations
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
        night_kill: str | None = None,
    ) -> tuple[str | None, dict[str, PlayerMemory]]:
        """
        Run day phase.

        Returns:
            (eliminated_player, updated_memories)
        """
        event_log.add_phase_start(
            state.phase,
            state.round_number,
            stage="phase_start",
            state_public=state.get_public_snapshot(),
        )
        transcript_manager.start_round(state.round_number, night_kill)

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
            )

            memories[speaker_name] = response.updated_memory

            speech_text = response.output.get("speech", "")
            nomination = response.output.get("nomination", "")

            if nomination and nomination not in nominations and state.is_alive(nomination):
                nominations.append(nomination)
                state.add_nomination(nomination)

            transcript_manager.add_speech(speaker_name, speech_text, nomination)
            event_log.add_speech(
                speaker_name,
                speech_text,
                nomination,
                response.output,
                phase=state.phase,
                round_number=state.round_number,
                stage="discussion",
                state_public=state.get_public_snapshot(),
            )

        # Voting phase
        votes = {}
        vote_details: dict[str, dict] = {}
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
            )

            memories[voter_name] = response.updated_memory
            votes[voter_name] = response.output.get("vote", "skip")
            vote_details[voter_name] = response.output
            state.record_vote(voter_name, votes[voter_name])

        # Resolve vote
        result = self.vote_resolver.resolve(votes, len(speaking_order))
        eliminated = None
        last_words: str | None = None
        defense_speeches: list[DefenseSpeech] | None = None
        revote: dict[str, str] | None = None
        revote_outcome: str | None = None

        if result.outcome == "eliminated":
            eliminated = result.eliminated
            last_words = await self._get_last_words(
                agents[eliminated],
                state,
                memories[eliminated],
            )
            state_before = state.get_public_snapshot()
            state.kill_player(eliminated)
            state_after = state.get_public_snapshot()
            event_log.add_vote(
                votes,
                f"eliminated:{eliminated}",
                eliminated,
                vote_details=vote_details,
                phase=state.phase,
                round_number=state.round_number,
                stage="vote",
                state_public=state_after,
                state_before=state_before,
                state_after=state_after,
            )
            event_log.add_last_words(
                eliminated,
                last_words,
                phase=state.phase,
                round_number=state.round_number,
                stage="last_words",
                state_public=state_after,
            )

        elif result.outcome == "revote":
            # Run revote
            (
                eliminated,
                last_words,
                defense_speeches,
                revote,
                revote_outcome,
                revote_details,
            ) = await self._run_revote(
                agents,
                state,
                transcript_manager,
                event_log,
                memories,
                result.tied_players or [],
                votes,
                result.vote_counts,
            )
            state_before = state.get_public_snapshot()
            if eliminated:
                state.kill_player(eliminated)
            state_after = state.get_public_snapshot()
            event_log.add_vote(
                votes,
                "revote",
                None,
                vote_details=vote_details,
                revote=revote,
                revote_outcome=revote_outcome,
                revote_details=revote_details,
                phase=state.phase,
                round_number=state.round_number,
                stage="vote",
                state_public=state_after,
                state_before=state_before,
                state_after=state_after,
            )
            if eliminated:
                event_log.add_last_words(
                    eliminated,
                    last_words,
                    phase=state.phase,
                    round_number=state.round_number,
                    stage="last_words",
                    state_public=state_after,
                )

        else:
            state_before = state.get_public_snapshot()
            event_log.add_vote(
                votes,
                "no_elimination",
                None,
                vote_details=vote_details,
                phase=state.phase,
                round_number=state.round_number,
                stage="vote",
                state_public=state_before,
                state_before=state_before,
                state_after=state_before,
            )

        # Finalize transcript
        vote_outcome = result.outcome
        if eliminated:
            vote_outcome = f"eliminated:{eliminated}"

        transcript_manager.finalize_round(
            round_number=state.round_number,
            night_kill=night_kill,
            votes=votes,
            vote_outcome=vote_outcome,
            last_words=last_words,
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
    ) -> str:
        """Get eliminated player's last words."""
        response = await agent.act(
            state.get_public_state(),
            [],
            memory,
            ActionType.LAST_WORDS,
        )
        return response.output.get("text", "")

    async def _run_revote(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        transcript_manager: TranscriptManager,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
        tied_players: list[str],
        votes: dict[str, str],
        vote_counts: dict[str, int],
    ) -> tuple[
        str | None,
        str | None,
        list[DefenseSpeech],
        dict[str, str],
        str,
        dict[str, dict],
    ]:
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
                action_context={"defense_context": defense_context},
            )
            text = response.output.get("text", "")
            defense_speeches.append(DefenseSpeech(speaker=name, text=text))
            event_log.add_defense(
                name,
                text,
                phase=state.phase,
                round_number=state.round_number,
                stage="defense",
                state_public=state.get_public_snapshot(),
            )

        # Revote
        revotes = {}
        revote_details: dict[str, dict] = {}
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
            )
            revotes[voter_name] = response.output.get("vote", "skip")
            revote_details[voter_name] = response.output

        result = self.vote_resolver.resolve_revote(
            revotes, len(speaking_order), tied_players
        )

        eliminated = None
        last_words: str | None = None
        if result.outcome == "eliminated":
            eliminated = result.eliminated
            last_words = await self._get_last_words(
                agents[eliminated],
                state,
                memories[eliminated],
            )
            # Last words are logged by the caller (DayPhase) to align with state snapshots.

        revote_outcome = result.outcome
        if eliminated:
            revote_outcome = f"eliminated:{eliminated}"

        return eliminated, last_words, defense_speeches, revotes, revote_outcome, revote_details


class NightPhase:
    """
    Night Phase: Mafia kill and Detective investigation.

    Night kills are silent - no last words collected.
    """

    async def run(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        transcript_manager: TranscriptManager,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
    ) -> tuple[str | None, dict[str, PlayerMemory]]:
        """
        Run night phase.

        Returns:
            (killed_player, updated_memories)
        """
        event_log.add_phase_start(
            state.phase,
            state.round_number,
            stage="phase_start",
            state_public=state.get_public_snapshot(),
        )

        transcript = transcript_manager.get_transcript_for_player(state.round_number)

        # Mafia coordination
        kill_target = await self._run_mafia_coordination(
            agents, state, transcript, event_log, memories
        )

        # Detective investigation
        await self._run_detective_investigation(
            agents, state, transcript, event_log, memories
        )

        # Execute kill (no last words - night kills are silent)
        if kill_target and kill_target in agents:
            state.kill_player(kill_target)

        return kill_target, memories

    async def _run_mafia_coordination(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        transcript: Transcript,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
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
                transcript,
                memories[agent.name],
                ActionType.NIGHT_KILL,
            )
            memories[agent.name] = response.updated_memory
            target = response.output.get("target", "skip")

            target = target if target != "skip" else None
            state_before = state.get_public_snapshot()
            state_after = state.get_public_snapshot_after_kill(target)
            event_log.add_night_kill(
                target,
                response.output,
                phase=state.phase,
                round_number=state.round_number,
                stage="night_kill",
                state_public=state_after,
                state_before=state_before,
                state_after=state_after,
            )
            return target

        # Sort by seat for deterministic order
        mafia_agents.sort(key=lambda a: a.seat)

        # Round 1: Sequential proposals
        proposals_r1 = {}
        proposals_r1_details: dict[str, dict] = {}

        first_mafia = mafia_agents[0]
        game_state = state.get_public_state()
        game_state.living_players = [
            p for p in game_state.living_players
            if p != first_mafia.name and p != first_mafia.partner
        ]

        first_response = await first_mafia.act(
            game_state,
            transcript,
            memories[first_mafia.name],
            ActionType.NIGHT_KILL,
        )
        memories[first_mafia.name] = first_response.updated_memory
        proposals_r1[first_mafia.name] = first_response.output.get("target", "skip")
        proposals_r1_details[first_mafia.name] = first_response.output

        second_mafia = mafia_agents[1]
        game_state = state.get_public_state()
        game_state.living_players = [
            p for p in game_state.living_players
            if p != second_mafia.name and p != second_mafia.partner
        ]

        second_response = await second_mafia.act(
            game_state,
            transcript,
            memories[second_mafia.name],
            ActionType.NIGHT_KILL,
            action_context={
                "round": 1,
                "partner_proposal": proposals_r1[first_mafia.name],
                "partner_message": proposals_r1_details[first_mafia.name].get("message", ""),
            },
        )
        memories[second_mafia.name] = second_response.updated_memory
        proposals_r1[second_mafia.name] = second_response.output.get("target", "skip")
        proposals_r1_details[second_mafia.name] = second_response.output

        targets = list(proposals_r1.values())

        # Check Round 1 agreement
        if targets[0] == targets[1]:
            target = targets[0] if targets[0] != "skip" else None
            state_before = state.get_public_snapshot()
            state_after = state.get_public_snapshot_after_kill(target)
            event_log.add_night_kill(
                target,
                {
                    "round": 1,
                    "proposals": proposals_r1,
                    "proposal_details": proposals_r1_details,
                },
                phase=state.phase,
                round_number=state.round_number,
                stage="night_kill",
                state_public=state_after,
                state_before=state_before,
                state_after=state_after,
            )
            return target

        if targets[0] == "skip" and targets[1] == "skip":
            state_before = state.get_public_snapshot()
            event_log.add_night_kill(
                None,
                {
                    "round": 1,
                    "proposals": proposals_r1,
                    "proposal_details": proposals_r1_details,
                },
                phase=state.phase,
                round_number=state.round_number,
                stage="night_kill",
                state_public=state_before,
                state_before=state_before,
                state_after=state_before,
            )
            return None

        # Round 2: Each sees partner's R1 proposal
        proposals_r2 = {}
        proposals_r2_details: dict[str, dict] = {}
        for agent in mafia_agents:
            partner_proposal = proposals_r1[agent.partner]
            game_state = state.get_public_state()
            game_state.living_players = [
                p for p in game_state.living_players
                if p != agent.name and p != agent.partner
            ]

            response = await agent.act(
                game_state,
                transcript,
                memories[agent.name],
                ActionType.NIGHT_KILL,
                action_context={
                    "round": 2,
                    "partner_proposal": partner_proposal,
                    "my_r1_proposal": proposals_r1[agent.name],
                    "partner_message": proposals_r1_details[agent.partner].get("message", ""),
                    "my_r1_message": proposals_r1_details[agent.name].get("message", ""),
                },
            )
            memories[agent.name] = response.updated_memory
            proposals_r2[agent.name] = response.output.get("target", "skip")
            proposals_r2_details[agent.name] = response.output

        targets_r2 = list(proposals_r2.values())

        # Check Round 2 agreement
        if targets_r2[0] == targets_r2[1]:
            target = targets_r2[0] if targets_r2[0] != "skip" else None
            state_before = state.get_public_snapshot()
            state_after = state.get_public_snapshot_after_kill(target)
            event_log.add_night_kill(
                target,
                {
                    "round": 2,
                    "proposals_r1": proposals_r1,
                    "proposals_r2": proposals_r2,
                    "proposal_details_r1": proposals_r1_details,
                    "proposal_details_r2": proposals_r2_details,
                },
                phase=state.phase,
                round_number=state.round_number,
                stage="night_kill",
                state_public=state_after,
                state_before=state_before,
                state_after=state_after,
            )
            return target

        # Still disagree: first Mafia (by seat) decides
        first_mafia = mafia_agents[0]
        target = proposals_r2[first_mafia.name]
        target = target if target != "skip" else None

        state_before = state.get_public_snapshot()
        state_after = state.get_public_snapshot_after_kill(target)
        event_log.add_night_kill(
            target,
            {
                "round": 2,
                "proposals_r1": proposals_r1,
                "proposals_r2": proposals_r2,
                "proposal_details_r1": proposals_r1_details,
                "proposal_details_r2": proposals_r2_details,
                "decided_by": first_mafia.name,
            },
            phase=state.phase,
            round_number=state.round_number,
            stage="night_kill",
            state_public=state_after,
            state_before=state_before,
            state_after=state_after,
        )
        return target

    async def _run_detective_investigation(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        transcript: Transcript,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
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
            transcript,
            memories[agent.name],
            ActionType.INVESTIGATION,
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
            event_log.add_investigation(
                target,
                result,
                response.output,
                phase=state.phase,
                round_number=state.round_number,
                stage="investigation",
                state_public=state.get_public_snapshot(),
            )
