import { Canvas } from '@react-three/fiber'
import Camera from './Camera'
import Lighting from './Lighting'
import Stage from './Stage'
import Characters from './Characters'
import { getArcPositions } from '../utils/layout'

function Scene({ players, activeSpeaker, living, phase, focusMode, subtitle }) {
  const positions = getArcPositions(players.length)
  const speakerIndex = activeSpeaker
    ? players.findIndex((player) => player.name === activeSpeaker)
    : -1
  const speakerPosition = speakerIndex >= 0 ? positions[speakerIndex] : null

  return (
    <div className="scene">
      <Canvas shadows>
        <Camera mode={focusMode} speakerPosition={speakerPosition} />
        <Lighting phase={phase} />
        <Stage />
        <Characters players={players} activeSpeaker={activeSpeaker} living={living} />
      </Canvas>
      {subtitle}
    </div>
  )
}

export default Scene
