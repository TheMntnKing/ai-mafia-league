function formatReasoning(reasoning) {
  if (!reasoning) return ''
  if (typeof reasoning === 'string') return reasoning
  if (typeof reasoning !== 'object') return ''

  if (reasoning.message) return reasoning.message
  if (reasoning.reasoning) return reasoning.reasoning
  if (reasoning.strategy) return reasoning.strategy
  if (reasoning.suspicions) return reasoning.suspicions
  if (reasoning.observations) return reasoning.observations

  return ''
}

function getSubtitleData(event, override) {
  if (override) return override
  if (!event) return null

  const data = event.data || {}

  if (data.text) {
    return {
      speaker: data.speaker || 'Unknown',
      label: null,
      text: data.text,
    }
  }

  if (event.type === 'elimination') {
    const eliminated = data.eliminated || 'Player'
    return {
      speaker: 'Narrator',
      label: null,
      text: `${eliminated} is eliminated.`,
    }
  }

  if (event.type === 'investigation') {
    const reasoning = formatReasoning(data.reasoning)
    if (!reasoning) return null
    return {
      speaker: 'Detective',
      label: null,
      text: reasoning,
    }
  }

  if (event.type === 'night_kill') {
    const text = formatReasoning(data.reasoning) || 'Mafia selects a target.'
    const target = data.target ? ` Target: ${data.target}.` : ''
    return {
      speaker: 'Mafia',
      label: null,
      text: `${text}${target}`.trim(),
    }
  }

  return null
}

function Subtitles({ event, override }) {
  const subtitle = getSubtitleData(event, override)
  if (!subtitle?.text) return null

  return (
    <div className="subtitle">
      <div className="subtitle__speaker">
        {subtitle.speaker}
        {subtitle.label ? ` · ${subtitle.label}` : ''}
      </div>
      <div className="subtitle__text">{subtitle.text}</div>
    </div>
  )
}

export default Subtitles
