// Level generator that produces *guaranteed-solvable* boards.
//
// Construction insight: solving means removing arrows one at a time, each with
// a clear forward path at removal time. So if we *build* the board by placing
// arrows one at a time and only ever place an arrow whose forward path is
// currently empty, then removing them in reverse placement order is always a
// valid solution. (In fact, the latest-placed remaining arrow is always
// releasable, so no play order can dead-end.)

import { DIR_LIST, STARTING_LIVES } from './constants.js'
import { idx, isPathClear, countArrows } from './engine.js'

function mulberry32(seed) {
  let a = seed >>> 0
  return function () {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function shuffle(arr, rng) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

/**
 * Build a solvable board.
 * @param {number} rows
 * @param {number} cols
 * @param {{ fill?: number, seed?: number, rng?: () => number }} [opts]
 *   fill — target fraction of cells to occupy (0..1).
 * @returns {{ board: Array<?string>, rows: number, cols: number, arrows: number }}
 */
export function generateBoard(rows, cols, opts = {}) {
  const { fill = 0.8, seed } = opts
  const rng = opts.rng || (seed != null ? mulberry32(seed) : Math.random)

  const board = new Array(rows * cols).fill(null)
  const cells = []
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) cells.push([r, c])
  }
  shuffle(cells, rng)

  const target = Math.max(1, Math.floor(rows * cols * fill))
  let placed = 0

  for (const [r, c] of cells) {
    if (placed >= target) break
    // Directions whose path to the edge is currently unobstructed.
    const valid = DIR_LIST.filter((d) => isPathClear(board, r, c, d, rows, cols))
    if (valid.length === 0) continue
    board[idx(r, c, cols)] = valid[Math.floor(rng() * valid.length)]
    placed++
  }

  return { board, rows, cols, arrows: countArrows(board) }
}

/** Difficulty knobs that scale with the level number. */
export function levelConfig(level) {
  const size = Math.min(5 + Math.floor((level - 1) / 2), 12)
  const fill = Math.min(0.68 + (level - 1) * 0.02, 0.92)
  return { rows: size, cols: size, fill, lives: STARTING_LIVES }
}

/** Difficulty label shown in the HUD. */
export function difficultyLabel(level) {
  if (level <= 3) return 'Easy'
  if (level <= 8) return 'Medium'
  if (level <= 15) return 'Hard'
  return 'Expert'
}

/** Create a fresh game state for a given level. */
export function createGame(level) {
  const cfg = levelConfig(level)
  const { board, rows, cols, arrows } = generateBoard(cfg.rows, cfg.cols, {
    fill: cfg.fill,
  })
  return {
    level,
    board,
    rows,
    cols,
    arrows,
    lives: cfg.lives,
    status: 'playing', // 'playing' | 'won' | 'lost'
  }
}
