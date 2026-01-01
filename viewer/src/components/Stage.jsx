const SCENE_MATERIALS = {
  day: {
    floor: '#F5F3EF',
    table: '#D9DDE3',
    top: '#F5F3EF',
  },
  night: {
    floor: '#7A8696',
    table: '#9AA3AF',
    top: '#D9DDE3',
  },
  mafia: {
    floor: '#5C2A2A',
    table: '#7A3A3A',
    top: '#9C4B4B',
  },
  detective: {
    floor: '#1B2F5A',
    table: '#2B4C7E',
    top: '#3E63A8',
  },
}

function Stage({ sceneKind = 'day' }) {
  const palette = SCENE_MATERIALS[sceneKind] || SCENE_MATERIALS.day

  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <circleGeometry args={[8.5, 64]} />
        <meshPhysicalMaterial color={palette.floor} metalness={0} roughness={0.55} clearcoat={0.05} />
      </mesh>
      <mesh position={[0, 0.34, 0]} castShadow>
        <cylinderGeometry args={[0.9, 0.95, 0.68, 32]} />
        <meshPhysicalMaterial color={palette.table} metalness={0} roughness={0.5} clearcoat={0.05} />
      </mesh>
      <mesh position={[0, 0.72, 0]} castShadow>
        <cylinderGeometry args={[1.1, 1.1, 0.08, 48]} />
        <meshPhysicalMaterial color={palette.top} metalness={0} roughness={0.5} clearcoat={0.05} />
      </mesh>
    </group>
  )
}

export default Stage
