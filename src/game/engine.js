// Pure game logic for the Arrow Puzzle. No React, no DOM — fully testable.
//
// A board is a flat array of length rows*cols. Each entry is either a
// direction ('U' | 'D' | 'L' | 'R') or null for an empty cell.
//
// Rules:
//  - Tapping an arrow releases it *if* every cell along its straight path to
//    the board edge (in the direction it points) is empty.
//  - If the path is clear, the arrow flies off and is removed.
//  - If any cell blocks the path, nothing is released and a life is lost.
//  - Clear every arrow to win; run out of lives to lose.

import { DIRS } from './constants.js'

export const idx = (r, c, cols) => r * cols + c

export const inBounds = (r, c, rows, cols) =>
  r >= 0 && r < rows && c >= 0 && c < cols

/**
 * Every cell from the one just ahead of (r,c) to the board edge, in `dir`.
 * @returns {Array<[number, number]>}
 */
export function forwardCells(r, c, dir, rows, cols) {
  const [dr, dc] = DIRS[dir]
  const cells = []
  let nr = r + dr
  let nc = c + dc
  while (inBounds(nr, nc, rows, cols)) {
    cells.push([nr, nc])
    nr += dr
    nc += dc
  }
  return cells
}

/** True when nothing stands between (r,c) and the edge it points toward. */
export function isPathClear(board, r, c, dir, rows, cols) {
  for (const [nr, nc] of forwardCells(r, c, dir, rows, cols)) {
    if (board[idx(nr, nc, cols)] !== null) return false
  }
  return true
}

/** Count arrows still on the board. */
export function countArrows(board) {
  let n = 0
  for (const cell of board) if (cell !== null) n++
  return n
}

/**
 * Attempt to release the arrow at (r,c).
 *
 * @returns {{ state: object, result: 'released'|'blocked'|'none', dir: ?string }}
 *   `state` is a new game state (or the same reference when result is 'none').
 */
export function tryRelease(state, r, c) {
  if (state.status !== 'playing') return { state, result: 'none', dir: null }

  const i = idx(r, c, state.cols)
  const dir = state.board[i]
  if (!dir) return { state, result: 'none', dir: null }

  if (isPathClear(state.board, r, c, dir, state.rows, state.cols)) {
    const board = state.board.slice()
    board[i] = null
    const arrows = state.arrows - 1
    return {
      state: {
        ...state,
        board,
        arrows,
        status: arrows === 0 ? 'won' : 'playing',
      },
      result: 'released',
      dir,
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
    dir,
  }
}

/**
 * Greedily solve a board by repeatedly releasing any arrow whose path is clear.
 * Used by tests to prove a generated board is winnable. Returns true if the
 * board can be fully cleared. (Because removing an arrow only ever *clears*
 * other paths, a greedy order can never deadlock on a solvable board.)
 */
export function isSolvable(board, rows, cols) {
  const work = board.slice()
  let remaining = countArrows(work)
  while (remaining > 0) {
    let progressed = false
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const dir = work[idx(r, c, cols)]
        if (dir && isPathClear(work, r, c, dir, rows, cols)) {
          work[idx(r, c, cols)] = null
          remaining--
          progressed = true
        }
      }
    }
    if (!progressed) return false
  }
  return true
}
