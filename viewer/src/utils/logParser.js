export function parseLog(log, options = {}) {
  if (!log || !Array.isArray(log.events)) {
    return []
  }

  const mode = options.mode || 'public'

  return log.events
    .map((event, index) => normalizeEvent(event, index, mode))
    .filter(Boolean)
}

function normalizeEvent(event, index, mode) {
  const data = event?.data || {}
  const privateFields = Array.isArray(event?.private_fields) ? event.private_fields : []
  const publicData = { ...data }

  privateFields.forEach((key) => {
    delete publicData[key]
  })

  const hasPublicFields = Object.keys(publicData).length > 0
  const isPublic = hasPublicFields
  const isNightZero = event?.type === 'night_zero_strategy'

  if (mode === 'public' && (!isPublic || isNightZero)) {
    return null
  }

  const visibleData = mode === 'public' ? publicData : data

  return {
    index,
    type: event?.type || 'unknown',
    timestamp: event?.timestamp || '',
    phase: data.phase || 'unknown',
    roundNumber: data.round_number ?? null,
    stage: data.stage || event?.type || 'unknown',
    statePublic: data.state_public || null,
    data: visibleData,
    rawData: data,
  }
}

export function findActiveSpeaker(event) {
  if (!event) return ''

  const data = event.data || {}

  if (['speech', 'defense', 'last_words', 'night_zero_strategy'].includes(event.type)) {
    return data.speaker || ''
  }

  return ''
}
