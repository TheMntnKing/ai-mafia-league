import { PerspectiveCamera } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useSpring } from '@react-spring/three'
import { useEffect, useMemo, useRef } from 'react'
import { Vector3 } from 'three'

const WIDE = {
  position: new Vector3(0, 3.5, 9),
  target: new Vector3(0, 0.8, 0),
}

function Camera({ mode, speakerPosition }) {
  const cameraRef = useRef(null)

  const [{ position, target }, api] = useSpring(() => ({
    position: WIDE.position.toArray(),
    target: WIDE.target.toArray(),
    config: { tension: 140, friction: 22 },
  }))

  const speakerPreset = useMemo(() => {
    if (!speakerPosition) return null
    const [x, y, z] = speakerPosition
    const position = new Vector3(x * 0.9, 2.6, 5.8)
    const target = new Vector3(x, y + 0.8, z)
    return { position, target }
  }, [speakerPosition])

  useEffect(() => {
    if (mode === 'vote') return
    const preset = mode === 'speaker' && speakerPreset ? speakerPreset : WIDE
    api.start({
      position: preset.position.toArray(),
      target: preset.target.toArray(),
    })
  }, [mode, speakerPreset, api])

  useFrame((state) => {
    const camera = cameraRef.current
    if (!camera) return

    if (mode === 'vote') {
      const t = state.clock.elapsedTime * 0.15
      const radius = 8
      camera.position.set(Math.sin(t) * radius, 3.2, Math.cos(t) * radius)
      camera.lookAt(0, 0.8, 0)
      return
    }

    const pos = position.get()
    const tgt = target.get()
    camera.position.set(pos[0], pos[1], pos[2])
    camera.lookAt(tgt[0], tgt[1], tgt[2])
  })

  return <PerspectiveCamera ref={cameraRef} makeDefault fov={45} />
}

export default Camera
