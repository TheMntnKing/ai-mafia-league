import Character from './Character'
import { getArcPositions, getFacingRotation } from '../utils/layout'

const COLORS = ['#2F7AE5', '#E54B4B', '#F2C94C', '#2ECC71', '#F2994A', '#8E44AD', '#3D4350']
const MODEL_BY_PERSONA = {
  tralalero_tralala: '/models/tralalelo.glb',
  bombardiro_crocodilo: '/models/brbrpatapim.glb',
}
const MODEL_BY_NAME = {
  'Tralalero Tralala': '/models/tralalelo.glb',
  'Bombardiro Crocodilo': '/models/brbrpatapim.glb',
}

const SCENE_CHARACTER_OFFSETS = {
  detective: [0.2, 0, 0.4],
  mafia: [0, 0, 0],
  night: [0, 0, 0],
  day: [0, 0, 0],
}

function Characters({ players, activeSpeaker, living, showRoles, sceneKind }) {
  const positions = getArcPositions(players.length)
  const faceCamera = sceneKind === 'detective'
  const sceneOffset = SCENE_CHARACTER_OFFSETS[sceneKind] || [0, 0, 0]

  return (
    <group>
      {players.map((player, index) => {
        const basePosition = positions[index] || [0, 0, 0]
        const position = [
          basePosition[0] + sceneOffset[0],
          basePosition[1] + sceneOffset[1],
          basePosition[2] + sceneOffset[2],
        ]
        const rotation = getFacingRotation(position)
        const isActive = activeSpeaker && player.name === activeSpeaker
        const isAlive = living ? living.includes(player.name) : true
        const color = COLORS[index % COLORS.length]

        const modelPath =
          MODEL_BY_PERSONA[player.persona_id] || MODEL_BY_NAME[player.name] || null

        return (
          <Character
            key={player.name}
            position={position}
            rotation={rotation}
            color={color}
            isActive={isActive}
            isAlive={isAlive}
            label={player.name}
            role={player.role}
            showRole={showRoles}
            modelPath={modelPath}
            faceCamera={faceCamera}
          />
        )
      })}
    </group>
  )
}

export default Characters
