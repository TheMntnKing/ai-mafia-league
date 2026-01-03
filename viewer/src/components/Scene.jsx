import { Canvas } from '@react-three/fiber'
import { Preload } from '@react-three/drei'
import Camera from './Camera'
import Lighting from './Lighting'
import Stage from './Stage'
import Characters from './Characters'
import { getArcPositions } from '../utils/layout'

const SCENE_LABELS = {
  mafia: 'Mafia Lair',
  detective: 'Detective Office',
  night: 'Night Falls',
}

function Scene({
  players,
  activeSpeaker,
  living,
  phase,
  focusMode,
  subtitle,
  voteOverlay,
  sceneKind,
  showRoles,
}) {
  const positions = getArcPositions(players.length)
  const speakerIndex = activeSpeaker
    ? players.findIndex((player) => player.name === activeSpeaker)
    : -1
  const speakerPosition = speakerIndex >= 0 ? positions[speakerIndex] : null
  const sceneLabel = SCENE_LABELS[sceneKind] || ''

  return (
    <div className="scene">
      <Canvas>
        <Camera mode={focusMode} speakerPosition={speakerPosition} sceneKind={sceneKind} />
        <Lighting phase={phase} scene={sceneKind} />
        <Stage sceneKind={sceneKind} />
        <Characters
          players={players}
          activeSpeaker={activeSpeaker}
          living={living}
          showRoles={showRoles}
          sceneKind={sceneKind}
        />
        <Preload all />
      </Canvas>
      {sceneLabel && <div className="scene-label">{sceneLabel}</div>}
      {subtitle}
      {voteOverlay}
    </div>
  )
}

export default Scene
