import { useEffect, useMemo, useState } from 'react'

function normalizePlayers(players = []) {
  const sorted = [...players].sort((a, b) => (a.seat ?? 0) - (b.seat ?? 0))
  const byName = {}
  sorted.forEach((player) => {
    byName[player.name] = player
  })
  return { sorted, byName }
}

function formatPhaseLabel(phase) {
  if (!phase || phase === 'unknown') return 'Phase'
  const [kind, num] = phase.split('_')
  if (kind === 'day') return `Day ${num || ''}`.trim()
  if (kind === 'night') return `Night ${num || ''}`.trim()
  if (kind === 'night' && !num) return 'Night'
  if (kind === 'night' || kind === 'day') return phase
  if (phase === 'night_zero') return 'Night Zero'
  return phase
}

function formatStageLabel(stage) {
  const map = {
    discussion: 'Discussion',
    vote: 'Vote',
    vote_result: 'Vote Result',
    revote: 'Revote',
    revote_result: 'Revote Result',
    defense: 'Defense',
    night_kill: 'Kill Planning',
    night_kill_result: 'Night Result',
    night_zero: 'Night Zero',
    investigation: 'Investigation',
    last_words: 'Last Words',
    game_end: 'Game End',
  }
  return map[stage] || stage || 'Stage'
}

function formatOutcome(outcome) {
  if (!outcome) return ''
  if (outcome.startsWith('eliminated:')) {
    return `${outcome.replace('eliminated:', '')} eliminated`
  }
  return outcome
}

function normalizeEvent(raw, index) {
  const data = raw?.data || {}
  const phase = data.phase || 'unknown'
  const roundNumber = data.round_number ?? null
  const stage = data.stage || raw.type || 'unknown'
  const privateFields = raw.private_fields || []
  const publicData = { ...data }
  privateFields.forEach((key) => {
    delete publicData[key]
  })
  const isPublic = Object.keys(publicData).length > 0
  return {
    index,
    type: raw.type || 'unknown',
    timestamp: raw.timestamp || '',
    data,
    phase,
    roundNumber,
    stage,
    statePublic: data.state_public || null,
    privateFields,
    publicData,
    isPublic,
  }
}

function buildPhaseIndex(events) {
  const index = {}
  events.forEach((event) => {
    const key = event.phase || 'unknown'
    if (!index[key]) {
      index[key] = []
    }
    index[key].push(event.index)
  })
  return index
}

function buildBeats(events, playersByName) {
  const beats = []
  const pendingDefense = {}

  const pushBeat = (base, overrides = {}) => {
    beats.push({ ...base, ...overrides, beatIndex: beats.length })
  }

  const insertBeforeNightResult = (beat) => {
    const idx = beats.findIndex(
      (existing) => existing.type === 'night_kill_result' && existing.phase === beat.phase
    )
    if (idx === -1) {
      pushBeat(beat)
      return
    }
    beats.splice(idx, 0, { ...beat, beatIndex: beats.length })
  }

  events.forEach((event) => {
    const data = event.data || {}
    const publicData = event.publicData || {}
    const phaseLabel = formatPhaseLabel(event.phase)

    if (event.type === 'phase_start') {
      return
    }

    if (event.type === 'speech') {
      pushBeat({
        type: 'speech',
        label: `${publicData.speaker || 'Player'} speaks`,
        speaker: publicData.speaker || '',
        text: publicData.text || '',
        nomination: publicData.nomination || '',
        reasoning: data.reasoning?.reasoning || '',
        phase: event.phase,
        stage: event.stage,
        statePublic: event.statePublic,
        isPublic: true,
      })
      return
    }

    if (event.type === 'night_zero_strategy') {
      pushBeat({
        type: 'night_zero',
        label: `${data.speaker || 'Mafia'} plan`,
        speaker: data.speaker || '',
        text: data.text || '',
        reasoning: data.reasoning?.reasoning || '',
        phase: event.phase,
        stage: event.stage,
        statePublic: event.statePublic,
        isPublic: false,
      })
      return
    }

    if (event.type === 'vote') {
      const voteStateBefore = data.state_before || event.statePublic || null
      const voteStateAfter = data.state_after || event.statePublic || null
      const votes = publicData.votes || {}
      const counts = {}
      Object.entries(votes).forEach(([voter, vote]) => {
        counts[vote] = (counts[vote] || 0) + 1
        const reasoning = data.vote_details?.[voter]?.reasoning || ''
        pushBeat({
          type: 'vote_cast',
          label: `${voter} votes ${vote}`,
          speaker: voter,
          target: vote,
          reasoning,
          phase: event.phase,
          stage: 'vote',
          statePublic: voteStateBefore,
          isPublic: true,
        })
      })

      if (publicData.outcome) {
        pushBeat({
          type: 'vote_result',
          label: `Vote result`,
          outcome: formatOutcome(publicData.outcome),
          text: Object.keys(counts).length
            ? Object.entries(counts)
                .map(([name, count]) => `${name}: ${count}`)
                .join(', ')
            : '',
          phase: event.phase,
          stage: 'vote_result',
          statePublic: voteStateAfter,
          isPublic: true,
        })
      }

      const defenseBeats = pendingDefense[event.phase] || []
      if (defenseBeats.length) {
        defenseBeats.forEach((beat) => pushBeat(beat))
        pendingDefense[event.phase] = []
      }

      const revotes = publicData.revote || {}
      const revoteCounts = {}
      Object.entries(revotes).forEach(([voter, vote]) => {
        revoteCounts[vote] = (revoteCounts[vote] || 0) + 1
        const reasoning = data.revote_details?.[voter]?.reasoning || ''
        pushBeat({
          type: 'revote_cast',
          label: `${voter} revotes ${vote}`,
          speaker: voter,
          target: vote,
          reasoning,
          phase: event.phase,
          stage: 'revote',
          statePublic: voteStateBefore,
          isPublic: true,
        })
      })

      if (publicData.revote_outcome) {
        pushBeat({
          type: 'revote_result',
          label: `Revote result`,
          outcome: formatOutcome(publicData.revote_outcome),
          text: Object.keys(revoteCounts).length
            ? Object.entries(revoteCounts)
                .map(([name, count]) => `${name}: ${count}`)
                .join(', ')
            : '',
          phase: event.phase,
          stage: 'revote_result',
          statePublic: voteStateAfter,
          isPublic: true,
        })
      }
      return
    }

    if (event.type === 'night_kill') {
      const details = data.reasoning || {}
      const stateBefore = data.state_before || event.statePublic || null
      const stateAfter = data.state_after || event.statePublic || null
      const proposalDetails = details.proposal_details || null
      if (proposalDetails) {
        const names = Object.keys(proposalDetails).sort((a, b) => {
          const seatA = playersByName[a]?.seat ?? 0
          const seatB = playersByName[b]?.seat ?? 0
          return seatA - seatB
        })
        names.forEach((name) => {
          const output = proposalDetails[name]
          pushBeat({
            type: 'mafia_proposal',
            label: `Mafia proposal`,
            speaker: name,
            target: output.target || '',
            text: output.message || '',
            reasoning: output.reasoning || '',
            phase: event.phase,
            stage: 'night_kill',
            statePublic: stateBefore,
            isPublic: false,
          })
        })
      }

      const r1Details = details.proposal_details_r1 || null
      const r2Details = details.proposal_details_r2 || null
      if (r1Details) {
        const names = Object.keys(r1Details).sort((a, b) => {
          const seatA = playersByName[a]?.seat ?? 0
          const seatB = playersByName[b]?.seat ?? 0
          return seatA - seatB
        })
        names.forEach((name) => {
          const output = r1Details[name]
          pushBeat({
            type: 'mafia_r1',
            label: `Mafia R1`,
            speaker: name,
            target: output.target || '',
            text: output.message || '',
            reasoning: output.reasoning || '',
            phase: event.phase,
            stage: 'night_kill',
            statePublic: stateBefore,
            isPublic: false,
          })
        })
      }
      if (r2Details) {
        const names = Object.keys(r2Details).sort((a, b) => {
          const seatA = playersByName[a]?.seat ?? 0
          const seatB = playersByName[b]?.seat ?? 0
          return seatA - seatB
        })
        names.forEach((name) => {
          const output = r2Details[name]
          pushBeat({
            type: 'mafia_r2',
            label: `Mafia R2`,
            speaker: name,
            target: output.target || '',
            text: output.message || '',
            reasoning: output.reasoning || '',
            phase: event.phase,
            stage: 'night_kill',
            statePublic: stateBefore,
            isPublic: false,
          })
        })
      }

      const target = publicData.target || 'none'
      pushBeat({
        type: 'night_kill_result',
        label: `Night kill`,
        target,
        phase: event.phase,
        stage: 'night_kill_result',
        statePublic: stateAfter,
        isPublic: true,
      })
      return
    }

    if (event.type === 'investigation') {
      const beat = {
        type: 'investigation',
        label: `Investigation: ${data.target || 'unknown'} is ${data.result || 'unknown'}`,
        speaker: 'Detective',
        target: data.target || '',
        outcome: data.result || '',
        reasoning: data.reasoning?.reasoning || '',
        phase: event.phase,
        stage: event.stage,
        statePublic: event.statePublic,
        isPublic: false,
      }
      insertBeforeNightResult(beat)
      return
    }

    if (event.type === 'last_words') {
      pushBeat({
        type: 'last_words',
        label: `Last words`,
        speaker: publicData.speaker || '',
        text: publicData.text || '',
        phase: event.phase,
        stage: event.stage,
        statePublic: event.statePublic,
        isPublic: true,
      })
      return
    }

    if (event.type === 'defense') {
      const beat = {
        type: 'defense',
        label: `Defense`,
        speaker: publicData.speaker || '',
        text: publicData.text || '',
        phase: event.phase,
        stage: event.stage,
        statePublic: event.statePublic,
        isPublic: true,
      }
      if (!pendingDefense[event.phase]) {
        pendingDefense[event.phase] = []
      }
      pendingDefense[event.phase].push(beat)
      return
    }

    if (event.type === 'game_end') {
      pushBeat({
        type: 'game_end',
        label: `Game end`,
        phase: event.phase,
        stage: event.stage,
        statePublic: event.statePublic,
        isPublic: true,
      })
    }
  })

  Object.values(pendingDefense).forEach((beatsForPhase) => {
    beatsForPhase.forEach((beat) => pushBeat(beat))
  })

  beats.forEach((beat, index) => {
    beat.beatIndex = index
  })

  return beats
}

function buildVoteTokens(beats, currentBeatIndex, isOmniscient) {
  if (!beats.length || currentBeatIndex < 0) return { tokens: [], stage: '' }
  const current = beats[currentBeatIndex]
  if (!current) return { tokens: [], stage: '' }
  const phase = current.phase
  const stage = current.stage
  let castType = ''
  if (stage === 'vote' || stage === 'vote_result') {
    castType = 'vote_cast'
  } else if (stage === 'revote' || stage === 'revote_result') {
    castType = 'revote_cast'
  } else {
    return { tokens: [], stage: '' }
  }

  const latestByVoter = {}
  for (let i = 0; i <= currentBeatIndex; i += 1) {
    const beat = beats[i]
    if (!beat || beat.phase !== phase) continue
    if (!isOmniscient && !beat.isPublic) continue
    if (beat.type !== castType) continue
    if (!beat.speaker || !beat.target) continue
    latestByVoter[beat.speaker] = beat.target
  }
  const tokens = Object.entries(latestByVoter).map(([voter, target]) => ({
    voter,
    target,
  }))
  return { tokens, stage }
}

function buildNightTargets(beats, currentBeatIndex, isOmniscient) {
  if (!isOmniscient || currentBeatIndex < 0) return {}
  const current = beats[currentBeatIndex]
  if (!current || current.stage !== 'night_kill') return {}
  const phase = current.phase
  const targets = {}
  for (let i = 0; i <= currentBeatIndex; i += 1) {
    const beat = beats[i]
    if (!beat || beat.phase !== phase) continue
    if (!['mafia_proposal', 'mafia_r1', 'mafia_r2'].includes(beat.type)) continue
    if (!beat.target || !beat.speaker) continue
    if (!targets[beat.target]) {
      targets[beat.target] = new Set()
    }
    targets[beat.target].add(beat.speaker)
  }
  const result = {}
  Object.entries(targets).forEach(([target, speakers]) => {
    result[target] = Array.from(speakers)
  })
  return result
}

function formatTokenLabel(target, playersByName) {
  const seat = playersByName?.[target]?.seat
  if (seat !== undefined && seat !== null) {
    return `#${seat}`
  }
  if (!target) return '?'
  return target.slice(0, 1).toUpperCase()
}

function getArcPosition(index, total) {
  if (total <= 1) {
    return { left: 50, bottom: 260, scale: 1 }
  }
  const t = total === 1 ? 0.5 : index / (total - 1)
  const left = 10 + t * 80
  const arcFactor = 1 - Math.pow(2 * t - 1, 2)
  const bottomBase = 260
  const curveHeight = 60
  const bottom = bottomBase + arcFactor * curveHeight
  const scale = 0.9 + arcFactor * 0.2
  return { left, bottom, scale }
}

function getAvatarUrl(player) {
  if (!player) return ''
  if (player.avatar_url) return player.avatar_url
  if (player.avatar) return player.avatar
  if (player.portrait) return player.portrait
  if (player.persona_id) return `/avatars/${player.persona_id}.png`
  return ''
}

function getAvatarLabel(player) {
  if (!player?.name) return '?'
  return player.name.slice(0, 1).toUpperCase()
}

function buildDerivedLog(log) {
  const players = normalizePlayers(log.players || [])
  const events = (log.events || []).map((event, idx) => normalizeEvent(event, idx))
  const phaseIndex = buildPhaseIndex(events)
  const beats = buildBeats(events, players.byName)
  const beatPhaseIndex = buildPhaseIndex(
    beats.map((beat) => ({
      index: beat.beatIndex,
      phase: beat.phase,
    }))
  )
  return {
    log,
    players,
    events,
    phaseIndex,
    beats,
    beatPhaseIndex,
  }
}

function App() {
  const [logData, setLogData] = useState(null)
  const [currentBeatIndex, setCurrentBeatIndex] = useState(0)
  const [loadError, setLoadError] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [selectedPhase, setSelectedPhase] = useState('')
  const [isOmniscient, setIsOmniscient] = useState(false)
  const [showReasoning, setShowReasoning] = useState(false)
  const [focusPlayer, setFocusPlayer] = useState('')
  const [displayText, setDisplayText] = useState('')

  const derived = useMemo(() => {
    if (!logData) return null
    try {
      return buildDerivedLog(logData)
    } catch (error) {
      console.error('Failed to parse log data', error)
      return { error }
    }
  }, [logData])

  useEffect(() => {
    setCurrentBeatIndex(0)
    setSelectedPhase('')
    setFocusPlayer('')
  }, [logData])

  const currentBeat = derived?.beats?.[currentBeatIndex] || null
  const phases = derived ? Object.keys(derived.beatPhaseIndex) : []
  const visibleState = currentBeat?.statePublic || null

  const filteredBeatIndexes = useMemo(() => {
    if (!derived) return []
    let indexes = derived.beats.map((beat) => beat.beatIndex)
    if (selectedPhase) {
      indexes = derived.beatPhaseIndex[selectedPhase] || []
    }
    if (!isOmniscient) {
      indexes = indexes.filter((idx) => derived.beats[idx]?.isPublic)
    }
    if (focusPlayer) {
      indexes = indexes.filter((idx) => {
        const beat = derived.beats[idx]
        if (!beat) return false
        if (beat.speaker === focusPlayer) return true
        if (beat.target === focusPlayer) return true
        return false
      })
    }
    return indexes
  }, [derived, selectedPhase, focusPlayer, isOmniscient])

  const activeIndex = filteredBeatIndexes.indexOf(currentBeatIndex)
  const goToIndex = (nextIndex) => {
    if (!derived) return
    const maxIndex = derived.beats.length - 1
    const target = Math.max(0, Math.min(maxIndex, nextIndex))
    setCurrentBeatIndex(target)
  }

  const stepEvent = (direction) => {
    if (!filteredBeatIndexes.length) return
    const nextPos = Math.max(
      0,
      Math.min(filteredBeatIndexes.length - 1, activeIndex + direction)
    )
    setCurrentBeatIndex(filteredBeatIndexes[nextPos])
  }

  useEffect(() => {
    const onKeyDown = (event) => {
      if (!filteredBeatIndexes.length) return
      const target = event.target
      const tag = target?.tagName?.toLowerCase()
      if (tag === 'input' || tag === 'select' || tag === 'textarea' || target?.isContentEditable) {
        return
      }
      if (event.key === 'ArrowRight' || event.key === 'j') {
        event.preventDefault()
        const nextPos = Math.min(filteredBeatIndexes.length - 1, activeIndex + 1)
        setCurrentBeatIndex(filteredBeatIndexes[nextPos])
      }
      if (event.key === 'ArrowLeft' || event.key === 'k') {
        event.preventDefault()
        const nextPos = Math.max(0, activeIndex - 1)
        setCurrentBeatIndex(filteredBeatIndexes[nextPos])
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [filteredBeatIndexes, activeIndex])

  const handleFile = (file) => {
    if (!file) return
    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target.result)
        setLogData(parsed)
        setLoadError('')
      } catch (error) {
        setLoadError('Invalid JSON log file.')
      }
    }
    reader.readAsText(file)
  }

  const onFileChange = (event) => {
    const file = event.target.files?.[0]
    handleFile(file)
  }

  const onDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    const file = event.dataTransfer.files?.[0]
    handleFile(file)
  }

  const onDragOver = (event) => {
    event.preventDefault()
    setIsDragging(true)
  }

  const onDragLeave = () => {
    setIsDragging(false)
  }

  const activeSpeaker = currentBeat?.speaker || ''
  const beatText = currentBeat?.text || currentBeat?.label || ''
  const beatReasoning = currentBeat?.reasoning || ''
  const seatPositions = useMemo(() => {
    if (!derived || derived.error) return {}
    const positions = {}
    derived.players.sorted.forEach((player, index) => {
      positions[player.name] = getArcPosition(index, derived.players.sorted.length)
    })
    return positions
  }, [derived])
  const avatarUrls = useMemo(() => {
    if (!derived || derived.error) return {}
    const urls = {}
    derived.players.sorted.forEach((player) => {
      const url = getAvatarUrl(player)
      if (url) {
        urls[player.name] = url
      }
    })
    return urls
  }, [derived])
  const speakerPosition = seatPositions[activeSpeaker]
  const speakerLeft = speakerPosition ? speakerPosition.left : 50
  const speakerLabel = currentBeat?.speaker || 'Narrator'
  const bubbleAnchor = Math.min(85, Math.max(15, speakerLeft))
  const voteTokens = derived && !derived.error
    ? buildVoteTokens(derived.beats, currentBeatIndex, isOmniscient)
    : { tokens: [], stage: '' }
  const nightTargets = derived && !derived.error
    ? buildNightTargets(derived.beats, currentBeatIndex, isOmniscient)
    : {}
  const investigationTarget =
    isOmniscient && currentBeat?.type === 'investigation' ? currentBeat.target : ''

  const renderKeyValue = (label, value) => (
    <div className="detail-row">
      <div className="detail-label">{label}</div>
      <div className="detail-value">{value}</div>
    </div>
  )

  useEffect(() => {
    if (!beatText) {
      setDisplayText('')
      return
    }
    let index = 0
    setDisplayText('')
    const interval = setInterval(() => {
      index += 1
      setDisplayText(beatText.slice(0, index))
      if (index >= beatText.length) {
        clearInterval(interval)
      }
    }, 18)
    return () => clearInterval(interval)
  }, [beatText, currentBeat?.beatIndex])

  const focusEvents = useMemo(() => {
    if (!focusPlayer || !derived) return []
    return filteredBeatIndexes
      .map((idx) => derived.beats[idx])
      .filter((beat) => beat)
      .slice(0, 6)
  }, [focusPlayer, filteredBeatIndexes, derived])

  const dataPhase = currentBeat?.phase?.startsWith('night_') ? 'night' : 'day'

  return (
    <div className={`app${logData && derived && !derived?.error ? ' has-log' : ''}`} data-phase={dataPhase}>
      {!logData && (
        <header className="app-header">
          <div>
            <div className="app-title">Mafia Replay Viewer</div>
            <div className="app-subtitle">Phase-based replay of game logs</div>
          </div>
        </header>
      )}

      <main className="app-main">
        {!logData && (
          <div className="empty-state">
            <div className="empty-title">No log loaded yet.</div>
            <div className="empty-text">Load a game log to begin the replay.</div>
            <div
              className={`drop-zone${isDragging ? ' drag' : ''}`}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
            >
              <div>Drop a JSON log here</div>
              <div className="drop-sub">or choose a file</div>
              <input className="file-input" type="file" accept=".json" onChange={onFileChange} />
            </div>
            {loadError && <div className="error-text">{loadError}</div>}
          </div>
        )}

        {logData && derived?.error && (
          <div className="empty-state">
            <div className="empty-title">Log loaded but could not be parsed.</div>
            <div className="empty-text">Check the console for details.</div>
          </div>
        )}

        {logData && derived && !derived.error && (
          <div className="viewer-stage">
            <div className="top-bar">
              <div className="top-controls">
                <label className="button-like">
                  Load log
                  <input className="file-input" type="file" accept=".json" onChange={onFileChange} />
                </label>
                <div className="control-group">
                  <label className="toggle">
                    <input
                      type="checkbox"
                      checked={isOmniscient}
                      onChange={(event) => {
                        const next = event.target.checked
                        setIsOmniscient(next)
                        if (!next) {
                          setShowReasoning(false)
                        }
                      }}
                    />
                    <span>Omniscient</span>
                  </label>
                  <label className="toggle">
                    <input
                      type="checkbox"
                      checked={showReasoning}
                      disabled={!isOmniscient}
                      onChange={(event) => setShowReasoning(event.target.checked)}
                    />
                    <span>Reasoning</span>
                  </label>
                </div>
                <select
                  className="select select-compact"
                  value={selectedPhase}
                  onChange={(event) => {
                    setSelectedPhase(event.target.value)
                    setCurrentBeatIndex(0)
                  }}
                >
                  <option value="">All phases</option>
                  {phases.map((phase) => (
                    <option key={phase} value={phase}>
                      {formatPhaseLabel(phase)}
                    </option>
                  ))}
                </select>
                <select
                  className="select select-compact"
                  value={focusPlayer}
                  onChange={(event) => {
                    setFocusPlayer(event.target.value)
                    setCurrentBeatIndex(0)
                  }}
                >
                  <option value="">All players</option>
                  {derived.players.sorted.map((player) => (
                    <option key={player.name} value={player.name}>
                      {player.name}
                    </option>
                  ))}
                </select>
                <div className="nav-buttons">
                  <button className="nav-button" onClick={() => stepEvent(-1)}>
                    Prev
                  </button>
                  <button className="nav-button" onClick={() => stepEvent(1)}>
                    Next
                  </button>
                </div>
              </div>
            </div>

            <section className="stage stage-full">
              <div className="stage-container">
                <div className="table-phase">
                  {currentBeat
                    ? `${formatPhaseLabel(currentBeat.phase)} - ${formatStageLabel(
                        currentBeat.stage
                      )}`
                    : 'Phase - Stage'}
                </div>
                <div className="stage-background" />
                <div className="stage-actors">
                  {derived.players.sorted.map((player, index) => {
                    const position = getArcPosition(index, derived.players.sorted.length)
                    const isDead =
                      visibleState?.dead?.includes(player.name) ||
                      (visibleState && !visibleState.living?.includes(player.name))
                    const isSpeaker = player.name === activeSpeaker
                    const isNominated = (visibleState?.nominated || []).includes(player.name)
                    const mafiaSpeakers = nightTargets[player.name] || []
                    const showMafiaBadge =
                      mafiaSpeakers.length > 0 && currentBeat?.stage === 'night_kill'
                    const showInvestigationBadge =
                      investigationTarget === player.name &&
                      currentBeat?.stage === 'investigation'
                    const shouldDim = activeSpeaker && !isSpeaker
                    const droppedBottom = position.bottom + (isDead ? -30 : 0)
                    const scale = position.scale * (isSpeaker ? 1.1 : 1)
                    const avatarUrl = avatarUrls[player.name] || ''

                    return (
                      <div
                        key={player.name}
                        className={`seat${isDead ? ' dead' : ''}${
                          isSpeaker ? ' active' : ''
                        }${shouldDim ? ' dim' : ''}`}
                        style={{
                          left: `${position.left}%`,
                          bottom: `${droppedBottom}px`,
                          transform: `translateX(-50%) scale(${scale})`,
                        }}
                      >
                        <div
                          className={`seat-avatar${avatarUrl ? ' has-avatar' : ''}`}
                          style={avatarUrl ? { backgroundImage: `url(${avatarUrl})` } : undefined}
                        >
                          {!avatarUrl && (
                            <span className="seat-avatar-label">{getAvatarLabel(player)}</span>
                          )}
                        </div>
                        <div className="seat-info">
                          <div className="seat-badges">
                            {isNominated && <span className="seat-badge">Nominated</span>}
                            {showMafiaBadge && (
                              <span className="seat-badge seat-badge-kill">
                                Targeted by {mafiaSpeakers.join(', ')}
                              </span>
                            )}
                            {showInvestigationBadge && (
                              <span className="seat-badge seat-badge-investigation">
                                Investigated
                              </span>
                            )}
                          </div>
                          <div className="seat-name">{player.name}</div>
                          <div className="seat-meta">Seat {player.seat}</div>
                          {isOmniscient && <div className="seat-role">{player.role}</div>}
                          <div className="seat-state">{isDead ? 'Dead' : 'Alive'}</div>
                        </div>
                      </div>
                    )
                  })}
                </div>
                {voteTokens.tokens.length > 0 && (
                  <div className="vote-tokens">
                    {voteTokens.tokens.map((token) => {
                      const position = seatPositions[token.voter]
                      const targetPlayer = derived.players.byName?.[token.target]
                      const targetAvatar = targetPlayer ? getAvatarUrl(targetPlayer) : ''
                      if (!position) return null
                      return (
                        <div
                          key={`${token.voter}-${token.target}`}
                          className={`vote-token${
                            voteTokens.stage === 'revote' || voteTokens.stage === 'revote_result'
                              ? ' revote'
                              : ''
                          }`}
                          style={{
                            left: `${position.left}%`,
                            backgroundImage: targetAvatar ? `url(${targetAvatar})` : undefined,
                          }}
                        >
                          {targetAvatar
                            ? ''
                            : formatTokenLabel(token.target, derived.players.byName)}
                        </div>
                      )
                    })}
                  </div>
                )}
                {currentBeat && beatText && (
                  <div className="speaker-bubble" style={{ left: `${bubbleAnchor}%` }}>
                    <div className="speaker-bubble-inner">
                      <div className="speech-speaker">{speakerLabel}</div>
                      <div className="speech-text">{displayText}</div>
                      {showReasoning && isOmniscient && beatReasoning && (
                        <div className="speech-reasoning">{beatReasoning}</div>
                      )}
                      {showReasoning && isOmniscient && !beatReasoning && (
                        <div className="speech-reasoning muted">No reasoning provided.</div>
                      )}
                    </div>
                  </div>
                )}
                <div className="table-surface" />
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
