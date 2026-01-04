"""Game phase execution logic."""

from __future__ import annotations

from collections import Counter
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

    Sequential coordination where Mafia players share strategy by seat order.
    Later Mafia see earlier strategies before responding.
    All strategies are stored in each Mafia's memory for future reference.
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
        if not mafia_agents:
            return memories

        # Sort by seat so coordination order is deterministic
        mafia_agents.sort(key=lambda a: a.seat)
        strategies: dict[str, str] = {}

        for agent in mafia_agents:
            game_state = state.get_public_state()
            action_context: dict[str, object] = {"night_zero": True}
            if strategies:
                action_context["partner_strategies"] = dict(strategies)

            response = await agent.act(
                game_state,
                transcript=[],
                memory=memories[agent.name],
                action_type=ActionType.SPEAK,
                action_context=action_context,
            )
            memories[agent.name] = response.updated_memory
            strategy = response.output.get("speech", "")
            strategies[agent.name] = strategy
            event_log.add(
                "night_zero_strategy",
                {
                    "speaker": agent.name,
                    "text": strategy,
                    "reasoning": response.output,
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

        # Store all strategies in each Mafia's memory for future reference
        for agent in mafia_agents:
            memory = memories[agent.name]
            facts = dict(memory.facts)
            facts["night_zero_strategies"] = dict(strategies)
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

        for position, speaker_name in enumerate(speaking_order, start=1):
            agent = agents[speaker_name]
            game_state = state.get_public_state()
            game_state.nominated_players = nominations.copy()

            transcript = transcript_manager.get_transcript_for_player(state.round_number)

            response = await agent.act(
                game_state,
                transcript,
                memories[speaker_name],
                ActionType.SPEAK,
                action_context={
                    "speaking_order": {
                        "position": position,
                        "total": len(speaking_order),
                        "spoken": speaking_order[: position - 1],
                        "remaining": speaking_order[position:],
                    }
                },
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
        last_words_text: str | None = None
        last_words_output: dict[str, object] | None = None
        defense_speeches: list[DefenseSpeech] | None = None
        revote: dict[str, str] | None = None
        revote_outcome: str | None = None
        state_snapshot = state.get_public_snapshot()

        if result.outcome == "eliminated":
            eliminated = result.eliminated
            event_log.add_vote_round(
                votes,
                "eliminated",
                round=1,
                vote_details=vote_details,
                phase=state.phase,
                round_number=state.round_number,
                stage="vote",
                state_public=state_snapshot,
            )
            game_over = self._is_game_over_after_elimination(state, eliminated)
            last_words_output = await self._get_last_words(
                agents[eliminated],
                state,
                memories[eliminated],
                game_over,
            )
            last_words_text = ""
            if last_words_output:
                last_words_text = str(last_words_output.get("text", ""))
            event_log.add_last_words(
                eliminated,
                last_words_text or "",
                last_words_output,
                phase=state.phase,
                round_number=state.round_number,
                stage="last_words",
                state_public=state_snapshot,
            )
            state_before = state_snapshot
            state.kill_player(eliminated)
            state_after = state.get_public_snapshot()
            event_log.add_elimination(
                eliminated,
                phase=state.phase,
                round_number=state.round_number,
                stage="elimination",
                state_public=state_after,
                state_before=state_before,
                state_after=state_after,
            )

        elif result.outcome == "revote":
            event_log.add_vote_round(
                votes,
                "tie",
                round=1,
                vote_details=vote_details,
                phase=state.phase,
                round_number=state.round_number,
                stage="vote",
                state_public=state_snapshot,
            )
            # Run revote
            (
                eliminated,
                last_words_output,
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
            event_outcome = "no_elimination"
            if revote_outcome:
                if revote_outcome.startswith("eliminated:"):
                    event_outcome = "eliminated"
                else:
                    event_outcome = revote_outcome
            event_log.add_vote_round(
                revote,
                event_outcome,
                round=2,
                vote_details=revote_details,
                phase=state.phase,
                round_number=state.round_number,
                stage="vote",
                state_public=state_snapshot,
            )
            state_before = state_snapshot
            if eliminated:
                last_words_text = ""
                if last_words_output:
                    last_words_text = str(last_words_output.get("text", ""))
                event_log.add_last_words(
                    eliminated,
                    last_words_text or "",
                    last_words_output,
                    phase=state.phase,
                    round_number=state.round_number,
                    stage="last_words",
                    state_public=state_snapshot,
                )
                state.kill_player(eliminated)
                state_after = state.get_public_snapshot()
                event_log.add_elimination(
                    eliminated,
                    phase=state.phase,
                    round_number=state.round_number,
                    stage="elimination",
                    state_public=state_after,
                    state_before=state_before,
                    state_after=state_after,
                )

        else:
            event_log.add_vote_round(
                votes,
                "no_elimination",
                round=1,
                vote_details=vote_details,
                phase=state.phase,
                round_number=state.round_number,
                stage="vote",
                state_public=state_snapshot,
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
            last_words=last_words_text,
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
        game_over: bool,
    ) -> dict[str, object]:
        """Get eliminated player's last words output."""
        response = await agent.act(
            state.get_public_state(),
            [],
            memory,
            ActionType.LAST_WORDS,
            action_context={"game_over": game_over},
        )
        return response.output

    def _is_game_over_after_elimination(
        self, state: GameStateManager, eliminated: str
    ) -> bool:
        living = [
            p for p in state.players.values() if p.alive and p.name != eliminated
        ]
        mafia_count = sum(1 for p in living if p.role == "mafia")
        town_count = len(living) - mafia_count
        if mafia_count == 0:
            return True
        if mafia_count >= town_count:
            return True
        doctor_alive = any(p.alive and p.role == "doctor" for p in living)
        if not doctor_alive and mafia_count >= town_count - 1:
            return True
        return False

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
        dict[str, object] | None,
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
        for position, name in enumerate(tied_players, start=1):
            agent = agents[name]
            response = await agent.act(
                state.get_public_state(),
                transcript_manager.get_transcript_for_player(state.round_number),
                memories[name],
                ActionType.DEFENSE,
                action_context={
                    "defense_context": defense_context,
                    "speaking_order": {
                        "position": position,
                        "total": len(tied_players),
                        "spoken": tied_players[: position - 1],
                        "remaining": tied_players[position:],
                    },
                },
            )
            text = response.output.get("text", "")
            defense_speeches.append(DefenseSpeech(speaker=name, text=text))
            event_log.add_defense(
                name,
                text,
                response.output,
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
        last_words_output: dict[str, object] | None = None
        if result.outcome == "eliminated":
            eliminated = result.eliminated
            game_over = self._is_game_over_after_elimination(state, eliminated)
            last_words_output = await self._get_last_words(
                agents[eliminated],
                state,
                memories[eliminated],
                game_over,
            )
            # Last words are logged by the caller (DayPhase) to align with state snapshots.

        revote_outcome = result.outcome
        if eliminated:
            revote_outcome = f"eliminated:{eliminated}"

        return (
            eliminated,
            last_words_output,
            defense_speeches,
            revotes,
            revote_outcome,
            revote_details,
        )


class NightPhase:
    """
    Night Phase: Mafia kill, Doctor protection, Detective investigation.

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
        intended_kill = await self._run_mafia_coordination(
            agents, state, transcript, event_log, memories
        )

        # Doctor protection
        protected_target, doctor_output = await self._run_doctor_protection(
            agents, state, transcript, event_log, memories
        )

        # Detective investigation
        investigation = await self._run_detective_investigation(
            agents, state, transcript, event_log, memories
        )
        if investigation:
            self._record_detective_investigation_history(memories, *investigation)

        protected = bool(intended_kill and protected_target == intended_kill)
        actual_kill = intended_kill if intended_kill and not protected else None

        state_before = state.get_public_snapshot()
        state_after = state.get_public_snapshot_after_kill(actual_kill)
        event_log.add_night_resolution(
            intended_kill=intended_kill,
            protected=protected,
            actual_kill=actual_kill,
            phase=state.phase,
            round_number=state.round_number,
            stage="night_resolution",
            state_public=state_before,
            state_before=state_before,
            state_after=state_after,
        )

        # Execute kill (no last words - night kills are silent)
        if actual_kill and actual_kill in agents:
            state.kill_player(actual_kill)

        self._record_mafia_kill_history(memories, agents, intended_kill, protected)
        self._record_doctor_protection_history(
            memories, agents, protected_target, doctor_output
        )

        return actual_kill, memories

    def _record_mafia_kill_history(
        self,
        memories: dict[str, PlayerMemory],
        agents: dict[str, PlayerAgent],
        intended_kill: str | None,
        protected: bool,
    ) -> None:
        mafia_agents = [
            a for a in agents.values() if a.role == "mafia" and a.name in memories
        ]
        if not mafia_agents:
            return
        if intended_kill is None:
            outcome = "skipped"
        elif protected:
            outcome = "blocked"
        else:
            outcome = "killed"

        for agent in mafia_agents:
            memory = memories[agent.name]
            facts = dict(memory.facts)
            history = list(facts.get("mafia_kill_history", []))
            entry = {"target": intended_kill or "skip", "outcome": outcome}
            history.append(entry)
            facts["mafia_kill_history"] = history
            facts["last_mafia_kill"] = entry
            memories[agent.name] = PlayerMemory(
                facts=facts,
                beliefs=dict(memory.beliefs),
            )

    def _record_doctor_protection_history(
        self,
        memories: dict[str, PlayerMemory],
        agents: dict[str, PlayerAgent],
        protected_target: str | None,
        doctor_output: dict | None,
    ) -> None:
        if not protected_target:
            return
        doctor_agents = [
            a for a in agents.values() if a.role == "doctor" and a.name in memories
        ]
        if not doctor_agents:
            return
        for agent in doctor_agents:
            memory = memories[agent.name]
            facts = dict(memory.facts)
            history = list(facts.get("doctor_protection_history", []))
            entry = {
                "target": protected_target,
                "reasoning": (doctor_output or {}).get("reasoning", ""),
            }
            history.append(entry)
            facts["doctor_protection_history"] = history
            facts["last_doctor_protect"] = entry
            memories[agent.name] = PlayerMemory(
                facts=facts,
                beliefs=dict(memory.beliefs),
            )

    def _record_detective_investigation_history(
        self,
        memories: dict[str, PlayerMemory],
        detective_name: str,
        target: str,
        result: str,
        output: dict,
    ) -> None:
        memory = memories.get(detective_name)
        if not memory:
            return
        facts = dict(memory.facts)
        entry = {
            "target": target,
            "result": result,
            "reasoning": output.get("reasoning", ""),
        }
        results = list(facts.get("investigation_results", []))
        results.append({"target": target, "result": result})
        history = list(facts.get("investigation_history", []))
        history.append(entry)
        facts["investigation_results"] = results
        facts["investigation_history"] = history
        facts["last_investigation"] = entry
        memories[detective_name] = PlayerMemory(
            facts=facts,
            beliefs=dict(memory.beliefs),
        )

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

        def resolve_majority(proposals: dict[str, str]) -> str | None:
            if not proposals:
                return None
            counts = Counter(proposals.values())
            top_target, top_count = max(counts.items(), key=lambda item: item[1])
            if top_count > len(proposals) / 2:
                return top_target
            return None

        # Sort by seat for deterministic order
        mafia_agents.sort(key=lambda a: a.seat)

        state_snapshot = state.get_public_snapshot()

        # Round 1: sequential proposals
        proposals_r1: dict[str, str] = {}
        messages_r1: dict[str, str] = {}
        for agent in mafia_agents:
            action_context: dict[str, object] = {"round": 1}
            if proposals_r1:
                action_context["prior_proposals"] = dict(proposals_r1)
                if messages_r1:
                    action_context["prior_messages"] = dict(messages_r1)

            response = await agent.act(
                state.get_public_state(),
                transcript,
                memories[agent.name],
                ActionType.NIGHT_KILL,
                action_context=action_context,
            )
            memories[agent.name] = response.updated_memory
            target = response.output.get("target", "skip")
            proposals_r1[agent.name] = target
            messages_r1[agent.name] = response.output.get("message", "")
            event_log.add_mafia_discussion(
                speaker=agent.name,
                target=target,
                message=response.output.get("message", ""),
                reasoning=response.output,
                coordination_round=1,
                phase=state.phase,
                round_number=state.round_number,
                state_public=state_snapshot,
            )

        majority_r1 = resolve_majority(proposals_r1)
        if majority_r1 is not None:
            final_target = None if majority_r1 == "skip" else majority_r1
            event_log.add_mafia_vote(
                votes=proposals_r1,
                final_target=final_target,
                decided_by=None,
                coordination_round=1,
                phase=state.phase,
                round_number=state.round_number,
                state_public=state_snapshot,
            )
            return final_target

        # Round 2: each sees all round 1 proposals
        proposals_r2: dict[str, str] = {}
        for agent in mafia_agents:
            action_context = {
                "round": 2,
                "r1_proposals": dict(proposals_r1),
                "r1_messages": dict(messages_r1),
            }
            response = await agent.act(
                state.get_public_state(),
                transcript,
                memories[agent.name],
                ActionType.NIGHT_KILL,
                action_context=action_context,
            )
            memories[agent.name] = response.updated_memory
            target = response.output.get("target", "skip")
            proposals_r2[agent.name] = target
            event_log.add_mafia_discussion(
                speaker=agent.name,
                target=target,
                message=response.output.get("message", ""),
                reasoning=response.output,
                coordination_round=2,
                phase=state.phase,
                round_number=state.round_number,
                state_public=state_snapshot,
            )

        majority_r2 = resolve_majority(proposals_r2)
        decided_by = None
        if majority_r2 is None:
            decided_by = mafia_agents[0].name
            majority_r2 = proposals_r2[decided_by]

        final_target = None if majority_r2 == "skip" else majority_r2
        event_log.add_mafia_vote(
            votes=proposals_r2,
            final_target=final_target,
            decided_by=decided_by,
            coordination_round=2,
            phase=state.phase,
            round_number=state.round_number,
            state_public=state_snapshot,
        )
        return final_target

    async def _run_doctor_protection(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        transcript: Transcript,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
    ) -> tuple[str | None, dict | None]:
        """Run Doctor protection choice."""
        doctor_agents = [
            a for a in agents.values()
            if a.role == "doctor" and state.is_alive(a.name)
        ]

        if not doctor_agents:
            return None, None

        agent = doctor_agents[0]
        response = await agent.act(
            state.get_public_state(),
            transcript,
            memories[agent.name],
            ActionType.DOCTOR_PROTECT,
        )
        memories[agent.name] = response.updated_memory

        protected = response.output.get("target", "")
        if protected not in state.get_living_players():
            return None, response.output

        event_log.add_doctor_protection(
            protector=agent.name,
            protected=protected,
            reasoning=response.output,
            phase=state.phase,
            round_number=state.round_number,
            stage="doctor_choice",
            state_public=state.get_public_snapshot(),
        )
        return protected, response.output

    async def _run_detective_investigation(
        self,
        agents: dict[str, PlayerAgent],
        state: GameStateManager,
        transcript: Transcript,
        event_log: EventLog,
        memories: dict[str, PlayerMemory],
    ) -> tuple[str, str, str, dict] | None:
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
            event_log.add_investigation(
                target,
                result,
                response.output,
                phase=state.phase,
                round_number=state.round_number,
                stage="investigation",
                state_public=state.get_public_snapshot(),
            )
            return agent.name, target, result, response.output
        return None
