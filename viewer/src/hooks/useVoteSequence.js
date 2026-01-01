import { useEffect, useMemo, useState } from 'react'

export const VOTE_STEP_MS = 900
export const VOTE_FINISH_PAUSE_MS = 500

function orderVotes(votes, players) {
  if (!votes) return []
  const playerOrder = players.map((player) => player.name)
  const ordered = []
  const remaining = new Set(Object.keys(votes))

  playerOrder.forEach((name) => {
    if (remaining.has(name)) {
      ordered.push({ voter: name, target: votes[name] })
      remaining.delete(name)
    }
  })

  Array.from(remaining)
    .sort()
    .forEach((name) => {
      ordered.push({ voter: name, target: votes[name] })
    })

  return ordered
}

export function useVoteSequence(event, players) {
  const [phase, setPhase] = useState(null)
  const [revealed, setRevealed] = useState(0)
  const [isComplete, setIsComplete] = useState(true)

  const sequences = useMemo(() => {
    if (!event || event.type !== 'vote_round') {
      return { primary: [], round: null }
    }

    const primary = orderVotes(event.data?.votes || {}, players)
    const round = event.data?.round ?? null

    return { primary, round }
  }, [event, players])

  useEffect(() => {
    if (!event || event.type !== 'vote_round') {
      setPhase(null)
      setRevealed(0)
      setIsComplete(true)
      return undefined
    }

    const timers = []
    let cursor = 0

    setIsComplete(false)
    setPhase(sequences.round === 2 ? 'revote' : 'vote')
    setRevealed(0)

    sequences.primary.forEach((_, index) => {
      const delay = VOTE_STEP_MS * (index + 1)
      timers.push(setTimeout(() => setRevealed(index + 1), delay))
      cursor = delay
    })

    timers.push(setTimeout(() => setIsComplete(true), cursor + VOTE_FINISH_PAUSE_MS))

    return () => timers.forEach(clearTimeout)
  }, [event, sequences])

  return {
    phase,
    revealed,
    votes: sequences.primary,
    round: sequences.round,
    isComplete,
    hasVotes: sequences.primary.length > 0,
  }
}
