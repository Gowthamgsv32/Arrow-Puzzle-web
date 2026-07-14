import { DIRS } from './constants.js'

const cx = (c) => c + 0.5
const cy = (r) => r + 0.5

/**
 * Visible polyline points [x,y] (cell units) for an arrow. A length-1 arrow has
 * no real segment, so we synthesize a short stub in its heading direction so it
 * still shows a shaft + arrowhead.
 */
export function arrowPoints(arrow) {
  if (arrow.verts.length >= 2) return arrow.verts.map(([r, c]) => [cx(c), cy(r)])
  const [dr, dc] = DIRS[arrow.dir]
  const [r, c] = arrow.head
  return [
    [cx(c) - dc * 0.32, cy(r) - dr * 0.32],
    [cx(c) + dc * 0.12, cy(r) + dr * 0.12],
  ]
}

function pointsToD(pts) {
  return pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x},${y}`).join(' ')
}

export function arrowD(arrow) {
  return pointsToD(arrowPoints(arrow))
}

/**
 * Parameters for the "train" release animation: a releasing line slides out
 * head-first along its own path plus a straight exit beyond the board edge,
 * rendered as a single stroke-dash sliding forward along this travel path.
 */
export function computeTrain(arrow, rows, cols) {
  const pts = arrowPoints(arrow)
  let ownLen = 0
  for (let i = 1; i < pts.length; i++) {
    ownLen += Math.abs(pts[i][0] - pts[i - 1][0]) + Math.abs(pts[i][1] - pts[i - 1][1])
  }
  ownLen = Math.max(ownLen, 0.4)

  const [dr, dc] = DIRS[arrow.dir]
  const exitLen = Math.max(rows, cols) + 2
  const [hr, hc] = arrow.head
  const exit = [cx(hc) + dc * exitLen, cy(hr) + dr * exitLen]

  const d = pointsToD(pts) + ` L${exit[0]},${exit[1]}`
  const total = ownLen + exitLen
  const durMs = Math.min(1100, Math.max(340, Math.round(total * 55)))
  return { d, ownLen, total, durMs }
}
