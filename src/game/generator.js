// Level generator that produces *guaranteed-solvable* boards of multi-cell
// arrows.
//
// Construction: place arrows one at a time. Each new arrow's head must have a
// clear forward path to the edge (over cells already placed), and its body
// extends backward over currently-empty cells. Removing arrows in reverse
// placement order is then always a valid solution — and since removing an arrow
// only frees cells, no play order can ever dead-end.

import { DIRS, DIR_LIST, STARTING_LIVES } from './constants.js'
import { EMPTY, idx, inBounds, occupiedCells } from './engine.js'

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
 * Build a solvable board of lengthy arrows.
 * @param {number} rows
 * @param {number} cols
 * @param {{ fill?: number, maxLen?: number, seed?: number, rng?: () => number }} [opts]
 * @returns {{ grid: number[], arrows: object, rows: number, cols: number, count: number }}
 */
export function generateLevel(rows, cols, opts = {}) {
  const { fill = 0.82, maxLen = 5, seed } = opts
  const rng = opts.rng || (seed != null ? mulberry32(seed) : Math.random)

  const grid = new Array(rows * cols).fill(EMPTY)
  const arrows = {}
  const target = Math.max(1, Math.floor(rows * cols * fill))

  const heads = []
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) heads.push([r, c])
  shuffle(heads, rng)

  let id = 0
  let occupied = 0

  for (const [r, c] of heads) {
    if (occupied >= target) break
    if (grid[idx(r, c, cols)] !== EMPTY) continue // head cell must be empty

    for (const dir of shuffle(DIR_LIST.slice(), rng)) {
      const [dr, dc] = DIRS[dir]

      // 1) Head's forward path to the edge must be clear.
      let clear = true
      let fr = r + dr
      let fc = c + dc
      while (inBounds(fr, fc, rows, cols)) {
        if (grid[idx(fr, fc, cols)] !== EMPTY) {
          clear = false
          break
        }
        fr += dr
        fc += dc
      }
      if (!clear) continue

      // 2) Body extends backward over empty cells, up to maxLen.
      let maxAvail = 1
      let br = r - dr
      let bc = c - dc
      while (
        maxAvail < maxLen &&
        inBounds(br, bc, rows, cols) &&
        grid[idx(br, bc, cols)] === EMPTY
      ) {
        maxAvail++
        br -= dr
        bc -= dc
      }

      const len = 1 + Math.floor(rng() * maxAvail) // 1..maxAvail
      const arrow = { id, dir, len, r, c }
      for (const [cr, cc] of occupiedCells(arrow)) grid[idx(cr, cc, cols)] = id
      arrows[id] = arrow
      id++
      occupied += len
      break
    }
  }

  return { grid, arrows, rows, cols, count: Object.keys(arrows).length }
}

/** Difficulty knobs that scale with the level number. */
export function levelConfig(level) {
  const size = Math.min(5 + Math.floor((level - 1) / 2), 12)
  const fill = Math.min(0.72 + (level - 1) * 0.02, 0.92)
  const maxLen = Math.min(3 + Math.floor((level - 1) / 3), 6)
  return { rows: size, cols: size, fill, maxLen, lives: STARTING_LIVES }
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
  const { grid, arrows, rows, cols, count } = generateLevel(cfg.rows, cfg.cols, {
    fill: cfg.fill,
    maxLen: cfg.maxLen,
  })
  return {
    level,
    rows,
    cols,
    grid,
    arrows,
    count,
    lives: cfg.lives,
    status: 'playing', // 'playing' | 'won' | 'lost'
  }
}
