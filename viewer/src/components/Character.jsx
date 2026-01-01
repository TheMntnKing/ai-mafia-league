const DEAD_COLOR = '#9AA3AF'
const PLASTIC = {
  metalness: 0,
  roughness: 0.5,
  clearcoat: 0.05,
  specularIntensity: 0.3,
}

function Character({ color, position, rotation, isActive, isAlive }) {
  const baseColor = isAlive ? color : DEAD_COLOR
  const emissive = isActive ? '#F2C94C' : '#000000'
  const scale = isActive ? 1.08 : 1
  const sinkOffset = isAlive ? 0 : -0.6
  const [x, y, z] = position
  const anchoredPosition = [x, y + sinkOffset, z]

  return (
    <group position={anchoredPosition} rotation={rotation} scale={scale}>
      <mesh castShadow>
        <boxGeometry args={[0.7, 0.9, 0.45]} />
        <meshPhysicalMaterial
          color={baseColor}
          emissive={emissive}
          emissiveIntensity={0.25}
          {...PLASTIC}
        />
      </mesh>
      <mesh position={[0, 0.75, 0]} castShadow>
        <boxGeometry args={[0.85, 0.55, 0.55]} />
        <meshPhysicalMaterial
          color={baseColor}
          emissive={emissive}
          emissiveIntensity={0.2}
          {...PLASTIC}
        />
      </mesh>
      <mesh position={[0, -0.6, 0]} castShadow>
        <boxGeometry args={[0.5, 0.35, 0.35]} />
        <meshPhysicalMaterial color={baseColor} {...PLASTIC} />
      </mesh>
      {!isAlive && (
        <group position={[0, 0.78, 0.29]}>
          <mesh rotation={[0, 0, Math.PI / 4]}>
            <boxGeometry args={[0.14, 0.04, 0.02]} />
            <meshStandardMaterial color="#111111" />
          </mesh>
          <mesh rotation={[0, 0, -Math.PI / 4]}>
            <boxGeometry args={[0.14, 0.04, 0.02]} />
            <meshStandardMaterial color="#111111" />
          </mesh>
          <mesh position={[0.22, 0, 0]} rotation={[0, 0, Math.PI / 4]}>
            <boxGeometry args={[0.14, 0.04, 0.02]} />
            <meshStandardMaterial color="#111111" />
          </mesh>
          <mesh position={[0.22, 0, 0]} rotation={[0, 0, -Math.PI / 4]}>
            <boxGeometry args={[0.14, 0.04, 0.02]} />
            <meshStandardMaterial color="#111111" />
          </mesh>
        </group>
      )}
    </group>
  )
}

export default Character
