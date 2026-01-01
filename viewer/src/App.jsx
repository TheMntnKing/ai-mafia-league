import { useMemo } from 'react'
import Scene from './components/Scene'
import Subtitles from './components/Subtitles'
import useGameStore from './stores/gameStore'
import { findActiveSpeaker } from './utils/logParser'

function sortPlayers(players = []) {
  return [...players].sort((a, b) => (a.seat ?? 0) - (b.seat ?? 0))
}

const FOCUS_EVENTS = new Set(['speech', 'defense', 'last_words', 'night_zero_strategy'])

function App() {
  const { log, events, eventIndex, mode, setLog, setMode, nextEvent, prevEvent } = useGameStore()
  const currentEvent = events[eventIndex] || null

  const players = useMemo(() => sortPlayers(log?.players || []), [log])
  const activeSpeaker = findActiveSpeaker(currentEvent)
  const living = currentEvent?.statePublic?.living || null
  const phase = currentEvent?.phase || 'day_1'
  let focusMode = 'wide'
  if (currentEvent?.type === 'vote') {
    focusMode = 'vote'
  } else if (currentEvent && FOCUS_EVENTS.has(currentEvent.type)) {
    focusMode = 'speaker'
  }

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
          players={players}
          activeSpeaker={activeSpeaker}
          living={living}
          phase={phase}
          focusMode={focusMode}
          subtitle={<Subtitles event={currentEvent} />}
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
