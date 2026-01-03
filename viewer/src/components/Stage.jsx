import { useGLTF } from '@react-three/drei'
import { useMemo } from 'react'
import { Box3, Vector3 } from 'three'

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
}

const SCENE_MODELS = {
  detective: '/scenes/detective_office.glb',
}

const SCENE_TARGET_WIDTH = {
  detective: 5,
  mafia: 14,
  town: 18,
}
const DEFAULT_TARGET_WIDTH = 14
const SCENE_OFFSETS = {
  detective: [0, 0, -0.4],
  mafia: [0, 0, 0],
  town: [0, 0, 0],
}
const DEFAULT_SCENE_OFFSET = [0, 0, 0]

function SceneModel({ path, targetWidth, sceneOffset }) {
  const { scene: originalScene } = useGLTF(path)
  const scene = useMemo(() => {
    const cloned = originalScene.clone(true)
    cloned.position.set(0, 0, 0)
    cloned.rotation.set(0, 0, 0)
    cloned.scale.set(1, 1, 1)
    cloned.updateMatrixWorld(true)
    return cloned
  }, [originalScene])
  const { scaleFactor, basePosition } = useMemo(() => {
    const box = new Box3().makeEmpty()
    scene.updateWorldMatrix(true, true)
    box.setFromObject(scene)
    const size = box.getSize(new Vector3())
    const maxHorizontal = Math.max(size.x, size.z)
    const scaleFactor = maxHorizontal > 0 ? targetWidth / maxHorizontal : 1
    const center = box.getCenter(new Vector3())
    const baseOffset = new Vector3(-center.x, -box.min.y, -center.z)
    return {
      scaleFactor,
      basePosition: baseOffset.multiplyScalar(scaleFactor),
    }
  }, [scene, targetWidth])

  return (
    <group position={sceneOffset}>
      <primitive
        object={scene}
        scale={scaleFactor}
        position={basePosition}
      />
    </group>
  )
}

function ProceduralStage({ palette }) {
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[8.5, 64]} />
        <meshPhysicalMaterial color={palette.floor} metalness={0} roughness={0.55} clearcoat={0.05} />
      </mesh>
      <mesh position={[0, 0.34, 0]}>
        <cylinderGeometry args={[0.9, 0.95, 0.68, 32]} />
        <meshPhysicalMaterial color={palette.table} metalness={0} roughness={0.5} clearcoat={0.05} />
      </mesh>
      <mesh position={[0, 0.72, 0]}>
        <cylinderGeometry args={[1.1, 1.1, 0.08, 48]} />
        <meshPhysicalMaterial color={palette.top} metalness={0} roughness={0.5} clearcoat={0.05} />
      </mesh>
    </group>
  )
}

function Stage({ sceneKind = 'day' }) {
  const modelPath = SCENE_MODELS[sceneKind]

  if (modelPath) {
    const targetWidth = SCENE_TARGET_WIDTH[sceneKind] || DEFAULT_TARGET_WIDTH
    const sceneOffset = SCENE_OFFSETS[sceneKind] || DEFAULT_SCENE_OFFSET
    return (
      <SceneModel path={modelPath} targetWidth={targetWidth} sceneOffset={sceneOffset} />
    )
  }

  const palette = SCENE_MATERIALS[sceneKind] || SCENE_MATERIALS.day
  return <ProceduralStage palette={palette} />
}

export default Stage
