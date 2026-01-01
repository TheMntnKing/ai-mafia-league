import Character from './Character'
import { getArcPositions, getFacingRotation } from '../utils/layout'

const COLORS = ['#2F7AE5', '#E54B4B', '#F2C94C', '#2ECC71', '#F2994A', '#8E44AD', '#3D4350']

function Characters({ players, activeSpeaker, living }) {
  const positions = getArcPositions(players.length)

  return (
    <group>
      {players.map((player, index) => {
        const position = positions[index] || [0, 0, 0]
        const rotation = getFacingRotation(position)
        const isActive = activeSpeaker && player.name === activeSpeaker
        const isAlive = living ? living.includes(player.name) : true
        const color = COLORS[index % COLORS.length]

        return (
          <Character
            key={player.name}
            position={position}
            rotation={rotation}
            color={color}
            isActive={isActive}
            isAlive={isAlive}
          />
        )
      })}
    </group>
  )
}

export default Characters
