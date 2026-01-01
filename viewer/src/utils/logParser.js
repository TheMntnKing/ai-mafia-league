export function parseLog(log, options = {}) {
  if (!log || !Array.isArray(log.events)) {
    return []
  }

  const mode = options.mode || 'public'
  const events = []
  let lastStatePublic = null

  log.events.forEach((event) => {
    const data = event?.data || {}
    const statePublic = data.state_public || null
    const isDayStart = event?.type === 'phase_start' && isDayPhase(data.phase)
    let dayAnnouncement = null
    let eventForView = event

    if (isDayStart && statePublic && lastStatePublic) {
      const newlyDead = getNewlyDead(lastStatePublic, statePublic)
      if (newlyDead.length) {
        eventForView = {
          ...event,
          data: { ...data, state_public: lastStatePublic },
        }
        dayAnnouncement = buildDayAnnouncement(event, newlyDead, statePublic)
      }
    }

    const normalized = normalizeEvent(eventForView, events.length, mode)
    if (normalized) {
      events.push(normalized)
    }

    if (dayAnnouncement) {
      const normalizedAnnouncement = normalizeEvent(dayAnnouncement, events.length, mode)
      if (normalizedAnnouncement) {
        events.push(normalizedAnnouncement)
      }
    }

    if (statePublic) {
      lastStatePublic = statePublic
    }
  })

  return events
}

function normalizeEvent(event, index, mode) {
  const isNightKill = event?.type === 'night_kill'
  const isInvestigation = event?.type === 'investigation'
  if (mode === 'public' && (isNightKill || isInvestigation)) {
    return null
  }

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

  const meta = visibleData
  return {
    index,
    type: event?.type || 'unknown',
    timestamp: event?.timestamp || '',
    phase: meta.phase || 'unknown',
    roundNumber: meta.round_number ?? null,
    stage: meta.stage || event?.type || 'unknown',
    statePublic: meta.state_public || null,
    data: visibleData,
    rawData: data,
  }
}

function isDayPhase(phase) {
  return typeof phase === 'string' && phase.startsWith('day_')
}

function getNewlyDead(previous, current) {
  if (!previous || !current) return []
  const prevLiving = new Set(previous.living || [])
  const nextLiving = new Set(current.living || [])
  const newlyDead = []

  prevLiving.forEach((name) => {
    if (!nextLiving.has(name)) {
      newlyDead.push(name)
    }
  })

  return newlyDead
}

function buildDayAnnouncement(sourceEvent, eliminated, statePublic) {
  const data = sourceEvent?.data || {}
  const names = eliminated.join(', ')
  const verb = eliminated.length > 1 ? 'were' : 'was'
  const text = `${names} ${verb} killed during the night.`

  return {
    type: 'day_announcement',
    timestamp: sourceEvent?.timestamp || '',
    data: {
      speaker: 'Narrator',
      text,
      eliminated: eliminated.length === 1 ? eliminated[0] : eliminated,
      phase: data.phase || 'unknown',
      round_number: data.round_number ?? null,
      stage: 'announcement',
      state_public: statePublic,
    },
    private_fields: [],
  }
}

export function findActiveSpeaker(event) {
  if (!event) return ''

  const data = event.data || {}

  if (['speech', 'defense', 'last_words', 'night_zero_strategy'].includes(event.type)) {
    return data.speaker || ''
  }

  if (event.type === 'elimination') {
    return data.eliminated || data.player || ''
  }

  if (event.type === 'day_announcement') {
    if (Array.isArray(data.eliminated)) {
      return data.eliminated[0] || ''
    }
    return data.eliminated || ''
  }

  return ''
}
