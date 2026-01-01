import { useEffect } from 'react'
import { VOTE_FINISH_PAUSE_MS, VOTE_STEP_MS } from './useVoteSequence'
import { getNightDialogueEntries, NIGHT_DIALOGUE_STEP_MS } from './useNightDialogue'

const BASE_STEP_MS = 2200

function getVoteDuration(event) {
  if (!event) return BASE_STEP_MS
  const votes = event.data?.votes || {}
  const count = Object.keys(votes).length
  return Math.max(BASE_STEP_MS, count * VOTE_STEP_MS + VOTE_FINISH_PAUSE_MS)
}

function getNightDialogueDuration(event) {
  const entries = getNightDialogueEntries(event)
  if (!entries.length) return BASE_STEP_MS
  return Math.max(BASE_STEP_MS, entries.length * NIGHT_DIALOGUE_STEP_MS)
}

function getDuration(event) {
  if (!event) return BASE_STEP_MS

  switch (event.type) {
    case 'vote_round':
      return getVoteDuration(event)
    case 'speech':
    case 'defense':
    case 'last_words':
      return 4200
    case 'night_kill':
    case 'investigation':
    case 'night_zero_strategy':
      return getNightDialogueDuration(event)
    case 'day_announcement':
      return 3000
    case 'elimination':
      return 3000
    default:
      return BASE_STEP_MS
  }
}

export function usePlayback({
  playing,
  event,
  events,
  eventIndex,
  nextEvent,
  setPlaying,
}) {
  useEffect(() => {
    if (!playing) return undefined
    if (!events.length || eventIndex >= events.length - 1) {
      setPlaying(false)
      return undefined
    }

    const delay = getDuration(event)
    const timer = setTimeout(() => {
      nextEvent()
    }, delay)

    return () => clearTimeout(timer)
  }, [playing, event, events.length, eventIndex, nextEvent, setPlaying])
}
