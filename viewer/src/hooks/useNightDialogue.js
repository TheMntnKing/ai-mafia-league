import { useEffect, useMemo, useState } from 'react'

export const NIGHT_DIALOGUE_STEP_MS = 2600

function formatLine(payload) {
  if (!payload) return ''
  if (typeof payload === 'string') return payload
  if (typeof payload !== 'object') return ''

  if (payload.message) return payload.message
  if (payload.speech) return payload.speech
  if (payload.text) return payload.text

  return ''
}

function buildEntriesForRound(details, proposals, roundLabel) {
  const entries = []
  const order = proposals ? Object.keys(proposals) : Object.keys(details || {})

  order.forEach((name) => {
    const payload = details?.[name] || {}
    let text = formatLine(payload)
    if (!text && proposals && proposals[name]) {
      text = `Proposes ${proposals[name]}`
    }
    if (!text) return
    entries.push({
      speaker: name,
      label: roundLabel,
      text,
    })
  })

  return entries
}

function buildNightKillEntries(reasoning) {
  if (!reasoning || typeof reasoning !== 'object') return []

  if (reasoning.proposal_details_r1 || reasoning.proposal_details_r2) {
    const entries = []
    entries.push(
      ...buildEntriesForRound(
        reasoning.proposal_details_r1,
        reasoning.proposals_r1,
        'R1'
      )
    )
    entries.push(
      ...buildEntriesForRound(
        reasoning.proposal_details_r2,
        reasoning.proposals_r2,
        'R2'
      )
    )
    return entries
  }

  if (reasoning.proposal_details) {
    const roundLabel = reasoning.round ? `R${reasoning.round}` : null
    return buildEntriesForRound(reasoning.proposal_details, reasoning.proposals, roundLabel)
  }

  const fallback = formatLine(reasoning)
  return fallback ? [{ speaker: 'Mafia', label: null, text: fallback }] : []
}

function buildEntries(event) {
  if (!event) return []
  const data = event.data || {}

  if (event.type === 'night_kill') {
    return buildNightKillEntries(data.reasoning)
  }

  if (event.type === 'night_zero_strategy') {
    const speaker = data.speaker || 'Mafia'
    if (data.text) {
      return [{ speaker, label: null, text: data.text }]
    }
    return []
  }

  if (event.type === 'investigation') {
    return []
  }

  return []
}

export function getNightDialogueEntries(event) {
  return buildEntries(event)
}

export function useNightDialogue(event) {
  const entries = useMemo(() => buildEntries(event), [event])
  const [index, setIndex] = useState(0)

  useEffect(() => {
    setIndex(0)
    if (entries.length <= 1) return undefined

    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % entries.length)
    }, NIGHT_DIALOGUE_STEP_MS)

    return () => clearInterval(timer)
  }, [entries])

  return entries[index] || null
}
