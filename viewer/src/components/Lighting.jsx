function Lighting({ phase, scene }) {
  const isNight = typeof phase === 'string' && phase.startsWith('night')

  if (scene === 'mafia') {
    return (
      <>
        <ambientLight intensity={0.28} color="#3B1A1A" />
        <directionalLight position={[5, 6, 4]} intensity={1.25} color="#FF4D4D" castShadow />
      </>
    )
  }

  if (scene === 'detective') {
    return (
      <>
        <ambientLight intensity={0.3} color="#15254A" />
        <directionalLight position={[5, 7, 4]} intensity={1.05} color="#4DA3FF" castShadow />
      </>
    )
  }

  if (isNight) {
    return (
      <>
        <ambientLight intensity={0.28} color="#7FA7FF" />
        <directionalLight
          position={[6, 8, 4]}
          intensity={0.85}
          color="#7FA7FF"
          castShadow
        />
      </>
    )
  }

  return (
    <>
      <ambientLight intensity={0.35} color="#BBD4FF" />
      <directionalLight
        position={[6, 10, 8]}
        intensity={1.15}
        color="#FFE6C7"
        castShadow
      />
    </>
  )
}

export default Lighting
