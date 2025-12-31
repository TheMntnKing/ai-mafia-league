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
    - Plurality winner is eliminated (unless "skip" wins)
    - Tie at top with most votes triggers revote (skip+single-player tie triggers revote)
    - If "skip" has the most votes or ties with 2+ players, no elimination
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
        # Count votes
        counts: dict[str, int] = {}
        for target in votes.values():
            counts[target] = counts.get(target, 0) + 1

        # Get player counts (excluding skip)
        player_counts = {k: v for k, v in counts.items() if k != "skip"}

        if not player_counts:
            # Everyone skipped
            return VoteResult(outcome="no_elimination", vote_counts=counts)

        max_votes = max(counts.values())
        tied = [p for p, c in counts.items() if c == max_votes]
        if len(tied) > 1:
            if "skip" in tied:
                non_skip = [p for p in tied if p != "skip"]
                if len(non_skip) == 1:
                    return VoteResult(
                        outcome="revote",
                        tied_players=non_skip,
                        vote_counts=counts,
                    )
                return VoteResult(outcome="no_elimination", vote_counts=counts)
            return VoteResult(
                outcome="revote",
                tied_players=tied,
                vote_counts=counts,
            )

        winner = tied[0]
        if winner == "skip":
            return VoteResult(outcome="no_elimination", vote_counts=counts)

        return VoteResult(outcome="eliminated", eliminated=winner, vote_counts=counts)

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
        # Count votes only for tied players
        counts: dict[str, int] = {}
        for target in votes.values():
            if target in tied_players or target == "skip":
                counts[target] = counts.get(target, 0) + 1

        player_counts = {k: v for k, v in counts.items() if k != "skip"}

        if not player_counts:
            return VoteResult(outcome="no_elimination", vote_counts=counts)

        max_votes = max(counts.values())
        tied = [p for p, c in counts.items() if c == max_votes]
        if len(tied) > 1:
            return VoteResult(outcome="no_elimination", vote_counts=counts)

        winner = tied[0]
        if winner == "skip":
            return VoteResult(outcome="no_elimination", vote_counts=counts)

        return VoteResult(outcome="eliminated", eliminated=winner, vote_counts=counts)
