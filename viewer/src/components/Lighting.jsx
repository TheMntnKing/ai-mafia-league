function Lighting({ phase, scene }) {
  const isNight = typeof phase === 'string' && phase.startsWith('night')

  if (scene === 'mafia') {
    // Red atmosphere but with fill light to preserve character colors
    return (
      <>
        <ambientLight intensity={0.3} color="#3B1A1A" />
        <directionalLight position={[5, 6, 4]} intensity={1.0} color="#FF4D4D" />
        <directionalLight position={[-3, 4, 8]} intensity={1.0} color="#ffffff" />
      </>
    )
  }

  if (scene === 'detective') {
    // Neutral lighting with soft fill (no blue noir)
    return (
      <>
        <ambientLight intensity={0.35} color="#D9DDE3" />
        <directionalLight position={[4, 6, 3]} intensity={0.9} color="#FFE6C7" />
        <directionalLight position={[-3, 4, 8]} intensity={0.6} color="#ffffff" />
      </>
    )
  }

  if (isNight) {
    // Cool moonlight with fill
    return (
      <>
        <ambientLight intensity={0.2} color="#7FA7FF" />
        <directionalLight position={[6, 8, 4]} intensity={0.6} color="#7FA7FF" />
        <directionalLight position={[-3, 4, 8]} intensity={0.3} color="#ffffff" />
      </>
    )
  }

  // Day: warm sunlight with cool fill
  return (
    <>
      <ambientLight intensity={0.4} color="#BBD4FF" />
      <directionalLight position={[6, 10, 8]} intensity={0.8} color="#FFE6C7" />
      <directionalLight position={[-3, 4, 8]} intensity={1.0} color="#ffffff" />
    </>
  )
}

export default Lighting
