// Pure game logic for the Arrow Puzzle. No React, no DOM — fully testable.
//
// Each arrow is a straight, multi-cell piece:
//   { id, dir, len, r, c }   where (r,c) is the HEAD (arrowhead) cell and the
//   body extends `len` cells backward, opposite `dir`.
//
// State:
//   { level, rows, cols, grid, arrows, count, lives, status }
//   - grid:   flat array, each cell holds an arrow id or -1 (empty)
//   - arrows: { [id]: arrow }
//   - count:  number of arrows remaining
//
// Rules:
//   - Tapping an arrow releases it *if* every cell ahead of its head (in `dir`,
//     up to the board edge) is empty. The whole piece then flies off.
//   - If any cell blocks that path, nothing is released and a life is lost.
//   - Clear every arrow to win; run out of lives to lose.

import { DIRS } from './constants.js'

export const EMPTY = -1

export const idx = (r, c, cols) => r * cols + c

export const inBounds = (r, c, rows, cols) =>
  r >= 0 && r < rows && c >= 0 && c < cols

/** All cells the arrow occupies (head first, then back along the body). */
export function occupiedCells(arrow) {
  const { dir, len, r, c } = arrow
  const [dr, dc] = DIRS[dir]
  const cells = []
  for (let k = 0; k < len; k++) cells.push([r - dr * k, c - dc * k])
  return cells
}

/** The bounding box of an arrow in cell units: { minR, minC, spanR, spanC }. */
export function boundingBox(arrow) {
  let minR = Infinity
  let minC = Infinity
  let maxR = -Infinity
  let maxC = -Infinity
  for (const [r, c] of occupiedCells(arrow)) {
    if (r < minR) minR = r
    if (r > maxR) maxR = r
    if (c < minC) minC = c
    if (c > maxC) maxC = c
  }
  return { minR, minC, spanR: maxR - minR + 1, spanC: maxC - minC + 1 }
}

/** Cells from just ahead of the head to the board edge, in `dir`. */
export function headForwardCells(arrow, rows, cols) {
  const { dir, r, c } = arrow
  const [dr, dc] = DIRS[dir]
  const out = []
  let nr = r + dr
  let nc = c + dc
  while (inBounds(nr, nc, rows, cols)) {
    out.push([nr, nc])
    nr += dr
    nc += dc
  }
  return out
}

/** True when nothing stands between the arrow's head and the edge it faces. */
export function isReleasable(grid, arrow, rows, cols) {
  for (const [nr, nc] of headForwardCells(arrow, rows, cols)) {
    if (grid[idx(nr, nc, cols)] !== EMPTY) return false
  }
  return true
}

/**
 * Attempt to release the arrow with id `id`.
 *
 * @returns {{ state: object, result: 'released'|'blocked'|'none', arrow: ?object }}
 */
export function tryRelease(state, id) {
  if (state.status !== 'playing') return { state, result: 'none', arrow: null }

  const arrow = state.arrows[id]
  if (!arrow) return { state, result: 'none', arrow: null }

  if (isReleasable(state.grid, arrow, state.rows, state.cols)) {
    const grid = state.grid.slice()
    for (const [r, c] of occupiedCells(arrow)) grid[idx(r, c, state.cols)] = EMPTY
    const arrows = { ...state.arrows }
    delete arrows[id]
    const count = state.count - 1
    return {
      state: {
        ...state,
        grid,
        arrows,
        count,
        status: count === 0 ? 'won' : 'playing',
      },
      result: 'released',
      arrow,
    }
  }

  const lives = state.lives - 1
  return {
    state: {
      ...state,
      lives,
      status: lives <= 0 ? 'lost' : 'playing',
    },
    result: 'blocked',
    arrow,
  }
}

/**
 * Greedily solve by repeatedly releasing any arrow whose head path is clear.
 * Returns true if the board can be fully cleared. Because removing an arrow
 * only ever *frees* cells, a greedy order can never deadlock a solvable board.
 */
export function isSolvable(gridIn, arrowsIn, rows, cols) {
  const grid = gridIn.slice()
  const arrows = { ...arrowsIn }
  let remaining = Object.keys(arrows).length
  while (remaining > 0) {
    let progressed = false
    for (const id of Object.keys(arrows)) {
      const arrow = arrows[id]
      if (isReleasable(grid, arrow, rows, cols)) {
        for (const [r, c] of occupiedCells(arrow)) grid[idx(r, c, cols)] = EMPTY
        delete arrows[id]
        remaining--
        progressed = true
      }
    }
    if (!progressed) return false
  }
  return true
}
