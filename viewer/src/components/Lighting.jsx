function Lighting({ phase }) {
  const isNight = typeof phase === 'string' && phase.startsWith('night')

  if (isNight) {
    return (
      <>
        <ambientLight intensity={0.18} color="#7FA7FF" />
        <directionalLight
          position={[6, 8, 4]}
          intensity={0.65}
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
