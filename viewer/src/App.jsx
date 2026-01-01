import { useMemo } from 'react'
import Scene from './components/Scene'
import Subtitles from './components/Subtitles'
import VoteTokens from './components/VoteTokens'
import useGameStore from './stores/gameStore'
import { findActiveSpeaker } from './utils/logParser'
import { useVoteSequence } from './hooks/useVoteSequence'
import { usePlayback } from './hooks/usePlayback'
import { useNightDialogue } from './hooks/useNightDialogue'

function sortPlayers(players = []) {
  return [...players].sort((a, b) => (a.seat ?? 0) - (b.seat ?? 0))
}

const FOCUS_EVENTS = new Set(['speech', 'defense', 'last_words', 'night_zero_strategy'])

function getSceneKind(event, mode) {
  if (!event) return 'day'
  if (mode !== 'omniscient') {
    return event.phase?.startsWith('night') ? 'night' : 'day'
  }
  if (event.type === 'night_zero_strategy' || event.type === 'night_kill') return 'mafia'
  if (event.type === 'investigation') return 'detective'
  if (event.phase?.startsWith('night')) return 'night'
  return 'day'
}

function getVisiblePlayers(players, event, mode) {
  if (mode !== 'omniscient') return players
  if (!event) return players
  if (event.type === 'night_zero_strategy' || event.type === 'night_kill') {
    return players.filter((player) => player.role === 'mafia')
  }
  if (event.type === 'investigation') {
    return players.filter((player) => player.role === 'detective')
  }
  return players
}

function ensureSpeakerAlive(living, speaker) {
  if (!living || !speaker) return living
  if (living.includes(speaker)) return living
  return [...living, speaker]
}

function getLivingForEvent(event, voteSequence, mode) {
  if (!event) return null
  const data = event.data || {}

  if (event.type === 'night_kill' && mode === 'omniscient') {
    return data.state_before?.living || data.state_public?.living || null
  }

  if (event.type === 'vote_round') {
    if (!voteSequence.isComplete) {
      return data.state_before?.living || data.state_public?.living || null
    }
    return data.state_after?.living || data.state_public?.living || null
  }

  if (event.type === 'last_words') {
    const living = data.state_before?.living || data.state_public?.living || null
    return ensureSpeakerAlive(living, data.speaker)
  }

  if (event.type === 'elimination') {
    return data.state_after?.living || data.state_public?.living || null
  }

  return data.state_public?.living || null
}

function App() {
  const {
    log,
    events,
    eventIndex,
    mode,
    playing,
    setLog,
    setMode,
    nextEvent,
    prevEvent,
    setPlaying,
    togglePlaying,
  } = useGameStore()
  const currentEvent = events[eventIndex] || null

  const players = useMemo(() => sortPlayers(log?.players || []), [log])
  const voteSequence = useVoteSequence(currentEvent, players)
  const nightDialogue = useNightDialogue(currentEvent)
  const activeSpeakerFromLog = findActiveSpeaker(currentEvent)
  const activeSpeaker =
    currentEvent?.type === 'night_kill' && nightDialogue?.speaker
      ? nightDialogue.speaker
      : activeSpeakerFromLog
  const phase = currentEvent?.phase || 'day_1'

  let focusMode = 'wide'
  if (currentEvent?.type === 'vote_round') {
    focusMode = 'vote'
  } else if (
    currentEvent?.type === 'elimination' ||
    currentEvent?.type === 'day_announcement'
  ) {
    focusMode = 'elimination'
  } else if (currentEvent && FOCUS_EVENTS.has(currentEvent.type)) {
    focusMode = 'speaker'
  }

  const living = getLivingForEvent(currentEvent, voteSequence, mode)
  const sceneKind = getSceneKind(currentEvent, mode)
  const scenePlayers = getVisiblePlayers(players, currentEvent, mode)

  usePlayback({
    playing,
    event: currentEvent,
    events,
    eventIndex,
    nextEvent,
    setPlaying,
  })

  const handleFile = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    const text = await file.text()
    const json = JSON.parse(text)
    setLog(json)
  }

  const eventLabel = currentEvent
    ? `${currentEvent.phase} · ${currentEvent.stage}`
    : 'No event loaded'

  const eventSpeaker = currentEvent?.data?.speaker || ''
  const eventText = currentEvent?.data?.text || ''
  const eventNomination = currentEvent?.data?.nomination || ''
  const defenseOverlay =
    currentEvent?.type === 'defense' ? (
      <div className="vote-overlay">
        <div className="vote-overlay__title">Defense Speeches</div>
      </div>
    ) : null
  const investigationOverlay =
    currentEvent?.type === 'investigation' ? (
      <div className="vote-overlay">
        <div className="vote-overlay__title">Investigation Result</div>
        <div className="vote-overlay__counts">
          {currentEvent.data?.target && (
            <div className="vote-count">Target: {currentEvent.data.target}</div>
          )}
          {currentEvent.data?.result && (
            <div className="vote-count">Result: {currentEvent.data.result}</div>
          )}
        </div>
      </div>
    ) : null

  return (
    <div className="app">
      <header className="toolbar">
        <div className="toolbar__left">
          <label className="file-input">
            <input type="file" accept="application/json" onChange={handleFile} />
            Load log JSON
          </label>
          <div className="mode-toggle">
            <span>Mode</span>
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="public">Public</option>
              <option value="omniscient">Omniscient</option>
            </select>
          </div>
        </div>
        <div className="toolbar__right">
          <button type="button" onClick={togglePlaying} disabled={!events.length}>
            {playing ? 'Pause' : 'Play'}
          </button>
          <button type="button" onClick={prevEvent} disabled={eventIndex <= 0}>
            Prev
          </button>
          <span className="event-count">
            {events.length ? `${eventIndex + 1} / ${events.length}` : '0 / 0'}
          </span>
          <button
            type="button"
            onClick={nextEvent}
            disabled={!events.length || eventIndex >= events.length - 1}
          >
            Next
          </button>
        </div>
      </header>

      <main className="content">
        <Scene
          players={scenePlayers}
          activeSpeaker={activeSpeaker}
          living={living}
          phase={phase}
          focusMode={focusMode}
          subtitle={<Subtitles event={currentEvent} override={nightDialogue} />}
          voteOverlay={
            currentEvent?.type === 'vote_round' ? (
              <VoteTokens sequence={voteSequence} />
            ) : (
              defenseOverlay || investigationOverlay
            )
          }
          sceneKind={sceneKind}
        />
        <aside className="event-panel">
          <div className="event-panel__label">{eventLabel}</div>
          <div className="event-panel__meta">
            {eventSpeaker ? `Speaker: ${eventSpeaker}` : 'Speaker: —'}
          </div>
          {eventText && <p className="event-panel__text">{eventText}</p>}
          {eventNomination && (
            <div className="event-panel__meta">Nomination: {eventNomination}</div>
          )}
          {!eventText && !eventNomination && (
            <div className="event-panel__meta">No speech text for this event.</div>
          )}
        </aside>
      </main>
    </div>
  )
}

export default App
