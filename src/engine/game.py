"""Game orchestration and main loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from src.engine.context import ContextBuilder
from src.engine.events import EventLog
from src.engine.phases import DayPhase, NightPhase, NightZeroPhase
from src.engine.state import GameStateManager
from src.engine.transcript import TranscriptManager
from src.players.agent import PlayerAgent
from src.schemas import PlayerMemory
from src.storage.json_logs import GameLogWriter

if TYPE_CHECKING:
    from src.providers.base import PlayerProvider
    from src.schemas import Persona


@dataclass
class GameConfig:
    """Configuration for a game run."""

    player_names: list[str]
    personas: dict[str, Persona]
    provider: PlayerProvider
    output_dir: str = "logs"
    seed: int | None = None


@dataclass
class GameResult:
    """Result of a completed game."""

    winner: str  # "town" or "mafia"
    rounds: int
    log_path: str
    final_living: list[str] = field(default_factory=list)
    eliminations: list[dict] = field(default_factory=list)


class GameRunner:
    """
    Orchestrates a complete Mafia game.

    Manages:
    - Game state
    - Player agents
    - Phase execution
    - Event logging
    - Result persistence
    """

    def __init__(self, config: GameConfig):
        self.config = config
        self.state = GameStateManager(config.player_names, config.seed)
        self.event_log = EventLog()
        self.transcript = TranscriptManager()
        self.context_builder = ContextBuilder()

        # Track game timing
        self.timestamp_start = datetime.now(UTC).isoformat()

        # Create player agents
        self.agents: dict[str, PlayerAgent] = {}
        self._create_agents()

        # Initialize player memories
        self.memories: dict[str, PlayerMemory] = {
            name: PlayerMemory(facts={}, beliefs={})
            for name in config.player_names
        }
        self.event_cursors: dict[str, int] = {
            name: 0 for name in config.player_names
        }

        # Phase runners
        self.night_zero = NightZeroPhase()
        self.day_phase = DayPhase()
        self.night_phase = NightPhase()

        # Track eliminations
        self.eliminations: list[dict] = []

    def _create_agents(self) -> None:
        """Create player agents with roles and partners."""
        for name in self.config.player_names:
            role = self.state.get_player_role(name)
            seat = self.state.get_player_seat(name)
            persona = self.config.personas[name]

            # Get Mafia partner if applicable
            partner = None
            if role == "mafia":
                partner = self.state.get_mafia_partner(name)

            self.agents[name] = PlayerAgent(
                name=name,
                persona=persona,
                role=role,
                seat=seat,
                provider=self.config.provider,
                partner=partner,
            )

    async def run(self) -> GameResult:
        """
        Run a complete game.

        Returns:
            GameResult with winner, rounds played, and log path
        """
        # Advance to night_zero before running Night Zero phase
        self.state.advance_phase()  # setup → night_zero

        # Night Zero: Mafia coordination
        self.memories = await self.night_zero.run(
            self.agents,
            self.state,
            self.event_log,
            self.memories,
            self.event_cursors,
        )

        night_kill: str | None = None

        # Main game loop
        while True:
            # Advance to day phase before running
            self.state.advance_phase()  # night_zero → day_1, night_N → day_(N+1)

            # Day Phase
            eliminated, self.memories = await self.day_phase.run(
                self.agents,
                self.state,
                self.transcript,
                self.event_log,
                self.memories,
                self.event_cursors,
                night_kill,
            )

            if eliminated:
                role = self.state.get_player_role(eliminated)
                self.eliminations.append({
                    "round": self.state.round_number,
                    "phase": "day",
                    "player": eliminated,
                    "role": role,
                })

            # Check win condition after day
            winner = self.state.check_win_condition()
            if winner:
                return await self._finalize_game(winner)

            # Advance to night phase before running
            self.state.advance_phase()  # day_N → night_N

            # Night Phase (no last words - night kills are silent)
            night_kill, self.memories = await self.night_phase.run(
                self.agents,
                self.state,
                self.event_log,
                self.memories,
                self.event_cursors,
            )

            if night_kill:
                role = self.state.get_player_role(night_kill)
                self.eliminations.append({
                    "round": self.state.round_number,
                    "phase": "night",
                    "player": night_kill,
                    "role": role,
                })

            # Check win condition after night
            winner = self.state.check_win_condition()
            if winner:
                return await self._finalize_game(winner)

            # Loop continues - advance_phase() at top of loop handles transition

    async def _finalize_game(self, winner: str) -> GameResult:
        """Finalize game and write log."""
        final_roles = self.state.get_all_roles()
        self.event_log.add_game_end(winner, final_roles)

        # Build log data
        log_data = self._build_log_data(winner)

        # Write log file
        writer = GameLogWriter(self.config.output_dir)
        log_path = await writer.write_game_log(log_data)

        return GameResult(
            winner=winner,
            rounds=self.state.round_number,
            log_path=log_path,
            final_living=self.state.get_living_players(),
            eliminations=self.eliminations,
        )

    def _build_log_data(self, winner: str) -> dict:
        """Build complete game log data per Phase 3 schema."""
        timestamp_end = datetime.now(UTC).isoformat()

        model = getattr(self.config.provider, "model", "unknown")
        if not isinstance(model, str):
            model = "unknown"

        # Build elimination lookup for player outcomes
        eliminated_players = {e["player"]: e["phase"] for e in self.eliminations}

        def get_outcome(name: str) -> str:
            """Calculate player outcome: survived, eliminated (day), or killed (night)."""
            if name in self.state.get_living_players():
                return "survived"
            phase = eliminated_players.get(name)
            return "killed" if phase == "night" else "eliminated"

        return {
            # Required fields per Phase 3 spec
            "schema_version": "1.0",
            "game_id": self.event_log.game_id,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": timestamp_end,
            "winner": winner,
            "players": [
                {
                    "seat": self.state.get_player_seat(name),
                    "persona_id": self.config.personas[name].identity.name,
                    "name": name,
                    "role": self.state.get_player_role(name),
                    "outcome": get_outcome(name),
                }
                for name in self.config.player_names
            ],
            "events": self.event_log.get_all_events(),
            # Extra fields for enrichment (not in Phase 3 spec but useful)
            "metadata": {
                "seed": self.config.seed,
                "model": model,
                "player_count": len(self.config.player_names),
            },
            "transcript": self.transcript.get_full_transcript(),
            "result": {
                "rounds": self.state.round_number,
                "final_living": self.state.get_living_players(),
                "eliminations": self.eliminations,
            },
        }


async def run_game(
    personas: dict[str, Persona],
    provider: PlayerProvider,
    output_dir: str = "logs",
    seed: int | None = None,
) -> GameResult:
    """
    Convenience function to run a game.

    Args:
        personas: Dict of player name -> Persona
        provider: LLM provider instance
        output_dir: Directory for game logs
        seed: Optional random seed

    Returns:
        GameResult with winner and log path
    """
    config = GameConfig(
        player_names=list(personas.keys()),
        personas=personas,
        provider=provider,
        output_dir=output_dir,
        seed=seed,
    )

    runner = GameRunner(config)
    return await runner.run()
