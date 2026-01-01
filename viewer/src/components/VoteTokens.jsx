import { useMemo } from 'react'

function buildCounts(votes) {
  return votes.reduce((acc, vote) => {
    const target = vote.target || 'skip'
    acc[target] = (acc[target] || 0) + 1
    return acc
  }, {})
}

function getPhaseLabel(sequence) {
  if (sequence.round === 2) return 'Revote'
  if (sequence.phase === 'revote') return 'Revote'
  return 'Voting'
}

function VoteTokens({ sequence }) {
  if (!sequence || !sequence.hasVotes) return null

  const visibleVotes = sequence.votes.slice(0, sequence.revealed)
  const counts = useMemo(() => buildCounts(visibleVotes), [visibleVotes])
  const phaseLabel = getPhaseLabel(sequence)

  return (
    <div className="vote-overlay">
      <div className="vote-overlay__title">{phaseLabel}</div>
      <div className="vote-overlay__list">
        {visibleVotes.map((vote, index) => (
          <div className="vote-chip" key={`${vote.voter}-${index}`}>
            <span className="vote-chip__voter">{vote.voter}</span>
            <span className="vote-chip__arrow">→</span>
            <span className="vote-chip__target">{vote.target}</span>
          </div>
        ))}
      </div>
      <div className="vote-overlay__counts">
        {Object.entries(counts).map(([target, count]) => (
          <div className="vote-count" key={target}>
            {target}: {count}
          </div>
        ))}
      </div>
    </div>
  )
}

export default VoteTokens
