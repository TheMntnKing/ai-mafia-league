import { animated, useSpring } from '@react-spring/three'
import { Html, useGLTF } from '@react-three/drei'
import { useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import { Box3, Color } from 'three'

const DEAD_COLOR = '#9AA3AF'
const DEAD_OFFSET = -0.6
const TARGET_HEIGHT = 1.7
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

function ModelMesh({ path, isAlive }) {
  const { scene: originalScene } = useGLTF(path)

  // Clone scene so each instance has its own copy (useGLTF returns shared/cached scene)
  const scene = useMemo(() => {
    const cloned = originalScene.clone(true)
    // Reset transform to ensure consistent bounding box calculation
    cloned.position.set(0, 0, 0)
    cloned.rotation.set(0, 0, 0)
    cloned.scale.set(1, 1, 1)
    cloned.updateMatrixWorld(true)
    return cloned
  }, [originalScene])

  const { scaleFactor, lift } = useMemo(() => {
    scene.updateMatrixWorld(true)
    const box = new Box3().setFromObject(scene)
    const height = box.max.y - box.min.y
    if (!Number.isFinite(height) || height <= 0) {
      return { scaleFactor: 1, lift: 0 }
    }
    // Subtract offset to compensate for models with geometry below visible feet
    const GROUND_OFFSET = 0.5
    return { scaleFactor: TARGET_HEIGHT / height, lift: -box.min.y - GROUND_OFFSET }
  }, [scene])

  useEffect(() => {
    scene.traverse((child) => {
      if (!child.isMesh) return
      child.frustumCulled = false
      if (child.geometry) {
        child.geometry.computeBoundingBox()
      }
      const materials = Array.isArray(child.material) ? child.material : [child.material]
      materials.forEach((material) => {
        if (!material) return
        if (!material.userData.baseColor) {
          const hasMap = Boolean(material.map)
          material.userData.baseColor = hasMap
            ? new Color('#ffffff')
            : material.color?.clone() || new Color('#ffffff')
        }
        // Apply plastic material properties (keep textures)
        Object.assign(material, {
          metalness: 0,
          roughness: 0.5,
          clearcoat: 0.05,
          clearcoatRoughness: 0.1,
        })
        if (material.type === 'MeshStandardMaterial' ||
            material.type === 'MeshPhysicalMaterial') {
          material.needsUpdate = true
        }
      })
    })
  }, [scene])

  useEffect(() => {
    const deadColor = new Color(DEAD_COLOR)
    scene.traverse((child) => {
      if (!child.isMesh) return
      const materials = Array.isArray(child.material) ? child.material : [child.material]
      materials.forEach((material) => {
        if (!material?.color) return
        if (isAlive) {
          const baseColor = material.userData.baseColor || new Color('#ffffff')
          material.color.copy(baseColor)
        } else {
          material.color.copy(deadColor)
        }
      })
    })
  }, [scene, isAlive])

  return (
    <primitive
      object={scene}
      scale={scaleFactor}
      position={[0, lift * scaleFactor, 0]}
    />
  )
}

function Character({
  color,
  position,
  rotation,
  isActive,
  isAlive,
  label,
  role,
  showRole,
  modelPath,
  faceCamera,
}) {
  const baseColor = isAlive ? color : DEAD_COLOR
  const emissive = isActive ? '#F2C94C' : '#000000'
  const scale = isActive ? 1.08 : 1
  const [x, y, z] = position
  const prevIsAlive = useRef(isAlive)
  const groupRef = useRef(null)
  const { camera } = useThree()
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
  const hasModel = Boolean(modelPath)
  const appliedRotation = faceCamera ? undefined : rotation

  useFrame(() => {
    if (!faceCamera || !groupRef.current) return
    groupRef.current.lookAt(camera.position.x, groupRef.current.position.y, camera.position.z)
  })

  return (
    <animated.group
      ref={groupRef}
      position={yOffset.to((offset) => [x, y + offset, z])}
      rotation={appliedRotation}
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
      {hasModel ? (
        <ModelMesh path={modelPath} isAlive={isAlive} />
      ) : (
        <>
          <mesh>
            <boxGeometry args={[0.7, 0.9, 0.45]} />
            <meshPhysicalMaterial
              color={baseColor}
              emissive={emissive}
              emissiveIntensity={0.25}
              {...PLASTIC}
            />
          </mesh>
          <mesh position={[0, 0.75, 0]}>
            <boxGeometry args={[0.85, 0.55, 0.55]} />
            <meshPhysicalMaterial
              color={baseColor}
              emissive={emissive}
              emissiveIntensity={0.2}
              {...PLASTIC}
            />
          </mesh>
          <mesh position={[0, -0.6, 0]}>
            <boxGeometry args={[0.5, 0.35, 0.35]} />
            <meshPhysicalMaterial color={baseColor} {...PLASTIC} />
          </mesh>
        </>
      )}
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

useGLTF.preload('/models/tralalelo.glb')
useGLTF.preload('/models/brbrpatapim.glb')
