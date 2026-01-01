function Subtitles({ event }) {
  if (!event) return null

  const text = event.data?.text
  if (!text) return null

  const speaker = event.data?.speaker || 'Unknown'

  return (
    <div className="subtitle">
      <div className="subtitle__speaker">{speaker}</div>
      <div className="subtitle__text">{text}</div>
    </div>
  )
}

export default Subtitles
