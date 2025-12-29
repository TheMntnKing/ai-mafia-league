"""Vote resolution logic."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VoteResult:
    """Result of a voting round."""

    outcome: str  # "eliminated", "no_elimination", "revote"
    eliminated: str | None = None
    tied_players: list[str] | None = None
    vote_counts: dict[str, int] = field(default_factory=dict)


class VoteResolver:
    """
    Resolves voting outcomes.

    Voting rules:
    - Majority (>50% of living players) eliminates target
    - Tie at top with most votes triggers revote
    - No majority and no tie means no elimination
    """

    def resolve(self, votes: dict[str, str], living_count: int) -> VoteResult:
        """
        Resolve vote outcome.

        Args:
            votes: Dict of voter -> target (or "skip")
            living_count: Number of living players

        Returns:
            VoteResult with outcome and details
        """
        majority_threshold = living_count // 2 + 1

        # Count votes
        counts: dict[str, int] = {}
        for target in votes.values():
            counts[target] = counts.get(target, 0) + 1

        # Get player counts (excluding skip)
        player_counts = {k: v for k, v in counts.items() if k != "skip"}

        if not player_counts:
            # Everyone skipped
            return VoteResult(outcome="no_elimination", vote_counts=counts)

        max_votes = max(player_counts.values())

        # Check for majority
        for player, count in player_counts.items():
            if count >= majority_threshold:
                return VoteResult(
                    outcome="eliminated",
                    eliminated=player,
                    vote_counts=counts,
                )

        # Check for tie at top
        tied = [p for p, c in player_counts.items() if c == max_votes]
        if len(tied) > 1:
            return VoteResult(
                outcome="revote",
                tied_players=tied,
                vote_counts=counts,
            )

        # No majority, no tie - no elimination
        return VoteResult(outcome="no_elimination", vote_counts=counts)

    def resolve_revote(
        self, votes: dict[str, str], living_count: int, tied_players: list[str]
    ) -> VoteResult:
        """
        Resolve a revote between tied players.

        Args:
            votes: Dict of voter -> target (or "skip")
            living_count: Number of living players voting
            tied_players: Players who were tied

        Returns:
            VoteResult - either eliminated or no_elimination (no second revote)
        """
        majority_threshold = living_count // 2 + 1

        # Count votes only for tied players
        counts: dict[str, int] = {}
        for target in votes.values():
            if target in tied_players or target == "skip":
                counts[target] = counts.get(target, 0) + 1

        player_counts = {k: v for k, v in counts.items() if k != "skip"}

        if not player_counts:
            return VoteResult(outcome="no_elimination", vote_counts=counts)

        # Check for majority
        for player, count in player_counts.items():
            if count >= majority_threshold:
                return VoteResult(
                    outcome="eliminated",
                    eliminated=player,
                    vote_counts=counts,
                )

        # Still tied or no majority - no elimination (no further revotes)
        return VoteResult(outcome="no_elimination", vote_counts=counts)
