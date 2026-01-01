import { create } from 'zustand'
import { parseLog } from '../utils/logParser'

const DEFAULT_MODE = 'public'

const clampIndex = (index, length) => {
  if (length <= 0) return 0
  return Math.max(0, Math.min(index, length - 1))
}

const useGameStore = create((set, get) => ({
  log: null,
  events: [],
  eventIndex: 0,
  mode: DEFAULT_MODE,
  playing: false,
  setLog: (log) => {
    const mode = get().mode
    const events = parseLog(log, { mode })
    set({ log, events, eventIndex: 0, playing: false })
  },
  setMode: (mode) => {
    const log = get().log
    const events = log ? parseLog(log, { mode }) : []
    set({ mode, events, eventIndex: 0, playing: false })
  },
  nextEvent: () =>
    set((state) => ({
      eventIndex: clampIndex(state.eventIndex + 1, state.events.length),
    })),
  prevEvent: () =>
    set((state) => ({
      eventIndex: clampIndex(state.eventIndex - 1, state.events.length),
    })),
  setIndex: (index) =>
    set((state) => ({
      eventIndex: clampIndex(index, state.events.length),
    })),
  setPlaying: (playing) => set({ playing }),
  togglePlaying: () => set((state) => ({ playing: !state.playing })),
}))

export default useGameStore
