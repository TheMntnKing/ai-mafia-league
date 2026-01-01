function Stage() {
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <circleGeometry args={[8.5, 64]} />
        <meshPhysicalMaterial color="#F5F3EF" metalness={0} roughness={0.55} clearcoat={0.05} />
      </mesh>
      <mesh position={[0, 0.34, 0]} castShadow>
        <cylinderGeometry args={[0.9, 0.95, 0.68, 32]} />
        <meshPhysicalMaterial color="#D9DDE3" metalness={0} roughness={0.5} clearcoat={0.05} />
      </mesh>
      <mesh position={[0, 0.72, 0]} castShadow>
        <cylinderGeometry args={[1.1, 1.1, 0.08, 48]} />
        <meshPhysicalMaterial color="#F5F3EF" metalness={0} roughness={0.5} clearcoat={0.05} />
      </mesh>
    </group>
  )
}

export default Stage
