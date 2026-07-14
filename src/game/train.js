import { DIRS } from './constants.js'

const cx = (c) => c + 0.5
const cy = (r) => r + 0.5

/**
 * Parameters for the "train" release animation: a releasing line slides out
 * head-first along its own path plus a straight exit beyond the board edge.
 * Rendered as a single stroke-dash sliding forward along this travel path.
 */
export function computeTrain(arrow, rows, cols) {
  const verts = arrow.verts
  let ownLen = 0
  for (let i = 1; i < verts.length; i++) {
    ownLen +=
      Math.abs(verts[i][0] - verts[i - 1][0]) +
      Math.abs(verts[i][1] - verts[i - 1][1])
  }

  const [dr, dc] = DIRS[arrow.dir]
  const exitLen = Math.max(rows, cols) + 2
  const [hr, hc] = arrow.head
  const exit = [hr + dr * exitLen, hc + dc * exitLen]

  const d =
    verts.map(([r, c], i) => `${i ? 'L' : 'M'}${cx(c)},${cy(r)}`).join(' ') +
    ` L${cx(exit[1])},${cy(exit[0])}`

  const total = ownLen + exitLen
  const durMs = Math.min(1100, Math.max(340, Math.round(total * 55)))
  return { d, ownLen, total, durMs }
}
