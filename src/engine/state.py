"""Game state management."""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.schemas import GameState


@dataclass
class PlayerInfo:
    """Internal player tracking (not exposed to LLM)."""

    name: str
    seat: int
    role: str  # "mafia", "detective", "doctor", "town"
    alive: bool = True


class GameStateManager:
    """
    Manages game state including players, phases, and win conditions.

    This class owns the authoritative game state. It tracks:
    - Player roles and alive status
    - Current phase and round number
    - Nominations and votes
    - Win condition detection
    """

    def __init__(self, player_names: list[str], seed: int | None = None):
        """
        Initialize game with players.

        Args:
            player_names: List of exactly 10 player names
            seed: Random seed for reproducibility (useful for testing)

        Raises:
            ValueError: If not exactly 10 players
        """
        if len(player_names) != 10:
            raise ValueError(f"Game requires exactly 10 players, got {len(player_names)}")

        self.rng = random.Random(seed)
        self.players: dict[str, PlayerInfo] = {}
        self.phase: str = "setup"
        self.round_number: int = 0
        self.nominations: list[str] = []
        self.votes: dict[str, str] = {}

        self._initialize_players(player_names)

    def _initialize_players(self, names: list[str]) -> None:
        """Assign random seats and roles to players."""
        # Shuffle for random seat assignment
        shuffled = names.copy()
        self.rng.shuffle(shuffled)

        # Assign roles: 3 Mafia, 1 Doctor, 1 Detective, 5 Town
        roles = ["mafia"] * 3 + ["doctor", "detective"] + ["town"] * 5
        self.rng.shuffle(roles)

        for seat, (name, role) in enumerate(zip(shuffled, roles, strict=True)):
            self.players[name] = PlayerInfo(name=name, seat=seat, role=role)

    def get_public_state(self) -> GameState:
        """
        Return the public-facing game state.

        This is what gets passed to players. It contains only
        information that should be visible to all players.
        """
        living = sorted(
            [p.name for p in self.players.values() if p.alive],
            key=lambda n: self.players[n].seat,
        )
        dead = sorted(
            [p.name for p in self.players.values() if not p.alive],
            key=lambda n: self.players[n].seat,
        )

        return GameState(
            phase=self.phase,
            round_number=self.round_number,
            living_players=living,
            dead_players=dead,
            nominated_players=self.nominations.copy(),
        )

    def get_public_snapshot(self) -> dict[str, object]:
        """Return a lightweight public snapshot for logs and replay."""
        state = self.get_public_state()
        return {
            "phase": state.phase,
            "round_number": state.round_number,
            "living": state.living_players,
            "dead": state.dead_players,
            "nominated": state.nominated_players,
        }

    def get_public_snapshot_after_kill(self, target: str | None) -> dict[str, object]:
        """Return a public snapshot as if target were killed (no state mutation)."""
        before = self.get_public_snapshot()
        if not target:
            return before
        living = [name for name in before["living"] if name != target]
        dead = before["dead"] + [target]
        living.sort(key=lambda name: self.players[name].seat)
        dead.sort(key=lambda name: self.players[name].seat)
        return {
            "phase": before["phase"],
            "round_number": before["round_number"],
            "living": living,
            "dead": dead,
            "nominated": before["nominated"],
        }

    def get_speaking_order(self) -> list[str]:
        """
        Get speaking order for current day.

        Speaking order rotates: first speaker position = (day_number - 1) mod player_count.
        Dead players are skipped.
        """
        # Get living players sorted by seat
        living = [p for p in self.players.values() if p.alive]
        living.sort(key=lambda p: p.seat)

        if not living:
            return []

        player_count = len(self.players)

        # Calculate starting position (rotates each day)
        # Day 1 -> start at seat 0, Day 2 -> start at seat 1, etc.
        day_number = self.round_number if self.round_number > 0 else 1
        start_offset = (day_number - 1) % player_count

        # Find the first living player at or after the start position
        # by rotating the living players list
        result = []

        # Find players in order starting from start_offset
        for offset in range(player_count):
            target_seat = (start_offset + offset) % player_count
            for player in living:
                if player.seat == target_seat and player.name not in result:
                    result.append(player.name)
                    break

        return result

    def get_mafia_partner(self, player_name: str) -> str | None:
        """
        Get the Mafia partner of a player.

        Args:
            player_name: Name of the player to check

        Returns:
            Partner's name if player is Mafia, None otherwise
        """
        player = self.players.get(player_name)
        if not player or player.role != "mafia":
            return None

        partners = self.get_mafia_partners(player_name)
        return partners[0] if partners else None

    def get_mafia_partners(self, player_name: str) -> list[str]:
        """
        Get all Mafia partners of a player (excluding self).

        Args:
            player_name: Name of the player to check

        Returns:
            List of Mafia partner names (empty if not Mafia)
        """
        player = self.players.get(player_name)
        if not player or player.role != "mafia":
            return []

        partners = [
            other.name
            for other in self.players.values()
            if other.role == "mafia" and other.name != player_name
        ]
        partners.sort(key=lambda name: self.players[name].seat)
        return partners

    def get_player_role(self, player_name: str) -> str | None:
        """Get a player's role."""
        player = self.players.get(player_name)
        return player.role if player else None

    def get_player_seat(self, player_name: str) -> int | None:
        """Get a player's seat number."""
        player = self.players.get(player_name)
        return player.seat if player else None

    def get_living_players(self) -> list[str]:
        """Get list of living player names."""
        living = [p for p in self.players.values() if p.alive]
        living.sort(key=lambda p: p.seat)
        return [p.name for p in living]

    def get_players_by_role(self, role: str) -> list[str]:
        """Get all players with a specific role."""
        players = [p for p in self.players.values() if p.role == role]
        players.sort(key=lambda p: p.seat)
        return [p.name for p in players]

    def get_living_players_by_role(self, role: str) -> list[str]:
        """Get living players with a specific role."""
        players = [p for p in self.players.values() if p.role == role and p.alive]
        players.sort(key=lambda p: p.seat)
        return [p.name for p in players]

    def is_alive(self, player_name: str) -> bool:
        """Check if a player is alive."""
        player = self.players.get(player_name)
        return player.alive if player else False

    def kill_player(self, name: str) -> None:
        """
        Mark a player as dead.

        Args:
            name: Name of the player to kill

        Raises:
            ValueError: If player doesn't exist or is already dead
        """
        player = self.players.get(name)
        if not player:
            raise ValueError(f"Unknown player: {name}")
        if not player.alive:
            raise ValueError(f"Player already dead: {name}")
        player.alive = False

    def check_win_condition(self) -> str | None:
        """
        Check if the game has ended.

        Returns:
            "town" if Town wins, "mafia" if Mafia wins, None if game continues
        """
        living = [p for p in self.players.values() if p.alive]
        mafia_count = sum(1 for p in living if p.role == "mafia")
        town_count = len(living) - mafia_count  # Includes Detective and Doctor

        # Town wins: all Mafia dead
        if mafia_count == 0:
            return "town"

        # Mafia wins: Mafia >= Town-aligned
        if mafia_count >= town_count:
            return "mafia"

        return None

    def check_forced_parity_after_day(self) -> str | None:
        """
        Check if Mafia win is guaranteed after the next night kill.

        Applies only when Doctor is dead and a day elimination just occurred.
        """
        living = [p for p in self.players.values() if p.alive]
        mafia_count = sum(1 for p in living if p.role == "mafia")
        town_count = len(living) - mafia_count
        doctor_alive = any(p.alive and p.role == "doctor" for p in self.players.values())

        if doctor_alive:
            return None

        if mafia_count >= town_count - 1:
            return "mafia"

        return None

    def advance_phase(self) -> str:
        """
        Advance to the next game phase.

        Phase progression:
        - setup -> night_zero
        - night_zero -> day_1
        - day_N -> night_N
        - night_N -> day_(N+1)

        Returns:
            The new phase name
        """
        phase_transitions = {
            "setup": "night_zero",
            "night_zero": "day_1",
        }

        if self.phase in phase_transitions:
            self.phase = phase_transitions[self.phase]
            if self.phase == "day_1":
                self.round_number = 1
        elif self.phase.startswith("day_"):
            day_num = int(self.phase.split("_")[1])
            self.phase = f"night_{day_num}"
        elif self.phase.startswith("night_"):
            night_num = int(self.phase.split("_")[1])
            self.phase = f"day_{night_num + 1}"
            self.round_number = night_num + 1

        # Reset nominations when entering a new day
        if self.phase.startswith("day_"):
            self.nominations = []
            self.votes = {}
        if self.phase.startswith("night_"):
            self.nominations = []
            self.votes = {}

        return self.phase

    def add_nomination(self, nominee: str) -> None:
        """Add a player to the nomination list."""
        if nominee not in self.players:
            raise ValueError(f"Unknown player: {nominee}")
        if not self.is_alive(nominee):
            raise ValueError(f"Cannot nominate dead player: {nominee}")
        if nominee not in self.nominations:
            self.nominations.append(nominee)

    def clear_nominations(self) -> None:
        """Clear all nominations."""
        self.nominations = []
        self.votes = {}

    def record_vote(self, voter: str, target: str) -> None:
        """
        Record a vote.

        Args:
            voter: Name of the voting player
            target: Name of the target or "skip"
        """
        if voter not in self.players:
            raise ValueError(f"Unknown voter: {voter}")
        if not self.is_alive(voter):
            raise ValueError(f"Cannot record vote from dead voter: {voter}")

        if target != "skip":
            if target not in self.players:
                raise ValueError(f"Unknown vote target: {target}")
            if not self.is_alive(target):
                raise ValueError(f"Cannot vote for dead player: {target}")
            if target not in self.nominations:
                raise ValueError(f"Vote target not nominated: {target}")

        self.votes[voter] = target

    def get_all_roles(self) -> dict[str, str]:
        """Get all player roles (for game end reveal)."""
        return {p.name: p.role for p in self.players.values()}
