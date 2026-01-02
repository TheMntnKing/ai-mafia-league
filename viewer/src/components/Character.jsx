import { animated, useSpring } from '@react-spring/three'
import { Html } from '@react-three/drei'
import { useEffect, useRef } from 'react'

const DEAD_COLOR = '#9AA3AF'
const DEAD_OFFSET = -0.6
const ROLE_COLORS = {
  mafia: '#E54B4B',
  detective: '#2F7AE5',
  villager: '#9AA3AF',
}
const PLASTIC = {
  metalness: 0,
  roughness: 0.5,
  clearcoat: 0.05,
  specularIntensity: 0.3,
}

function Character({ color, position, rotation, isActive, isAlive, label, role, showRole }) {
  const baseColor = isAlive ? color : DEAD_COLOR
  const emissive = isActive ? '#F2C94C' : '#000000'
  const scale = isActive ? 1.08 : 1
  const [x, y, z] = position
  const prevIsAlive = useRef(isAlive)
  const [{ yOffset }, api] = useSpring(() => ({
    yOffset: isAlive ? 0 : DEAD_OFFSET,
    config: { tension: 120, friction: 18 },
  }))

  useEffect(() => {
    if (prevIsAlive.current === isAlive) return
    if (isAlive) {
      api.start({ yOffset: 0, immediate: true })
    } else {
      api.start({ yOffset: DEAD_OFFSET })
    }
    prevIsAlive.current = isAlive
  }, [isAlive, api])

  const roleColor = ROLE_COLORS[role] || '#3D4350'

  return (
    <animated.group
      position={yOffset.to((offset) => [x, y + offset, z])}
      rotation={rotation}
      scale={scale}
    >
      {label && (
        <Html center position={[0, 1.6, 0]} distanceFactor={6}>
          <div className={`character-label${isActive ? ' character-label--active' : ''}`}>
            <span className="character-label__name">{label}</span>
            {showRole && role && (
              <span className="character-label__role" style={{ '--role-color': roleColor }}>
                {role}
              </span>
            )}
          </div>
        </Html>
      )}
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
    </animated.group>
  )
}

export default Character
