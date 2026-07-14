// Level generator: fill a shape completely with bent arrow lines, with NO gaps,
// and stay guaranteed-solvable.
//
// Method — "carve/peel": simulate clearing the shape. Repeatedly find a cell
// that could exit right now (a clear straight path from it to the board edge
// through already-removed / non-shape cells), make it a head, and grow a bent
// body backward into the still-present cells; remove them all. The order we
// carve is exactly a valid solve order, so:
//   - every shape cell ends up in some line  -> no interior gaps
//   - each line's head path is clear when it is released -> solvable
//   - removing a line only frees cells        -> no play order can dead-end

import { DIRS, DIR_LIST, STARTING_LIVES } from './constants.js'
import { EMPTY, idx, inBounds } from './engine.js'
import { SHAPE_NAMES, shapeMask } from './shapes.js'

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

// Straight path from (r,c) toward the edge in `dir` is clear when no cell along
// it is still present.
function clearToEdge(present, cols, rows, r, c, dir) {
  const [dr, dc] = DIRS[dir]
  let nr = r + dr
  let nc = c + dc
  while (inBounds(nr, nc, rows, cols)) {
    if (present.has(idx(nr, nc, cols))) return false
    nr += dr
    nc += dc
  }
  return true
}

// Ordered adjacent cells -> corner vertices (endpoints + direction changes).
function cellsToVerts(cells) {
  if (cells.length <= 2) return cells.slice()
  const verts = [cells[0]]
  for (let i = 1; i < cells.length - 1; i++) {
    const [pr, pc] = cells[i - 1]
    const [r, c] = cells[i]
    const [nr, nc] = cells[i + 1]
    if (r - pr !== nr - r || c - pc !== nc - c) verts.push(cells[i])
  }
  verts.push(cells[cells.length - 1])
  return verts
}

/**
 * Fully fill a shape mask with bent lines.
 * @returns {{ grid, arrows, rows, cols, count }}
 */
export function generateLevel(rows, cols, opts = {}) {
  const { mask, maxLen = 6, seed } = opts
  const rng = opts.rng || (seed != null ? mulberry32(seed) : Math.random)

  const grid = new Array(rows * cols).fill(EMPTY)
  const present = new Set(mask ? mask : Array.from({ length: rows * cols }, (_, i) => i))
  const arrows = {}
  let id = 0

  const has = (r, c) => inBounds(r, c, rows, cols) && present.has(idx(r, c, cols))

  // Choose a head: a present cell with a clear exit, preferring one whose body
  // can extend (so we make long bent lines, not single dots).
  function pickHead() {
    let fallback = null
    for (let t = 0; t < 50; t++) {
      const arr = [...present]
      const i = arr[Math.floor(rng() * arr.length)]
      const r = Math.floor(i / cols)
      const c = i % cols
      for (const d of shuffle(DIR_LIST.slice(), rng)) {
        if (!clearToEdge(present, cols, rows, r, c, d)) continue
        const [dr, dc] = DIRS[d]
        if (has(r - dr, c - dc)) return { r, c, dir: d } // extendable
        if (!fallback) fallback = { r, c, dir: d }
      }
    }
    if (fallback) return fallback
    // Guaranteed progress: the globally topmost present cell can always exit up.
    let best = null
    for (const i of present) {
      const r = Math.floor(i / cols)
      const c = i % cols
      if (!best || r < best.r || (r === best.r && c < best.c)) best = { r, c }
    }
    return { r: best.r, c: best.c, dir: 'U' }
  }

  while (present.size > 0) {
    const { r, c, dir } = pickHead()
    const [dr, dc] = DIRS[dir]

    // Body: head, then step opposite the exit dir, then wander with bends.
    const cells = [[r, c]] // head -> tail
    const used = new Set([idx(r, c, cols)])
    let cr = r - dr
    let cc = c - dc
    let lastR = -dr
    let lastC = -dc

    if (has(cr, cc) && !used.has(idx(cr, cc, cols))) {
      cells.push([cr, cc])
      used.add(idx(cr, cc, cols))
      while (cells.length < maxLen) {
        const options = []
        for (const d of DIR_LIST) {
          const [er, ec] = DIRS[d]
          const nr = cr + er
          const nc = cc + ec
          if (has(nr, nc) && !used.has(idx(nr, nc, cols))) options.push([er, ec, nr, nc])
        }
        if (!options.length) break
        // Prefer going straight for cleaner runs; otherwise turn randomly.
        const straight = options.find(([er, ec]) => er === lastR && ec === lastC)
        const pick = straight && rng() < 0.6 ? straight : options[Math.floor(rng() * options.length)]
        cr = pick[2]
        cc = pick[3]
        lastR = pick[0]
        lastC = pick[1]
        cells.push([cr, cc])
        used.add(idx(cr, cc, cols))
      }
    }

    const ordered = cells.slice().reverse() // tail -> head
    for (const [pr, pc] of ordered) {
      present.delete(idx(pr, pc, cols))
      grid[idx(pr, pc, cols)] = id
    }
    arrows[id] = {
      id,
      dir,
      head: [r, c],
      cells: ordered,
      verts: cellsToVerts(ordered),
    }
    id++
  }

  return { grid, arrows, rows, cols, count: Object.keys(arrows).length }
}

/** Difficulty knobs + which shape to fill, scaling with the level number. */
export function levelConfig(level) {
  const size = Math.min(20 + Math.floor((level - 1) / 4), 24)
  const maxLen = Math.min(5 + Math.floor((level - 1) / 3), 8)
  const shape = SHAPE_NAMES[(level - 1) % SHAPE_NAMES.length]
  return { rows: size, cols: size, maxLen, shape, lives: STARTING_LIVES }
}

const CAP = { heart: 'Heart', ball: 'Ball', star: 'Star', apple: 'Apple', diamond: 'Diamond' }
export function shapeLabel(shape) {
  return CAP[shape] || 'Shape'
}

/** Create a fresh game state for a given level. */
export function createGame(level) {
  const cfg = levelConfig(level)
  const mask = shapeMask(cfg.shape, cfg.rows)
  const { grid, arrows, rows, cols, count } = generateLevel(cfg.rows, cfg.cols, {
    mask,
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
    status: 'playing',
    shape: cfg.shape,
  }
}
