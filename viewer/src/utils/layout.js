export const ARC_LAYOUT = {
  radius: 4.5,
  centerZ: -1.8,
  startAngle: -Math.PI,
  endAngle: 0,
  y: 0.6,
}

export function getArcPositions(count, config = ARC_LAYOUT) {
  if (count <= 0) return []

  const { radius, centerZ, startAngle, endAngle, y } = config
  const step = count > 1 ? (endAngle - startAngle) / (count - 1) : 0

  return Array.from({ length: count }, (_, i) => {
    const angle = startAngle + step * i
    const x = Math.cos(angle) * radius
    const z = centerZ + Math.sin(angle) * radius
    return [x, y, z]
  })
}

export function getFacingRotation(position) {
  const [x, , z] = position
  const dx = -x
  const dz = -z
  const yaw = Math.atan2(dx, dz)
  return [0, yaw, 0]
}
