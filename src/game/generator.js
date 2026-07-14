// Level generator: random, non-overlapping, guaranteed-solvable BENT lines.
//
// Each line is a self-avoiding polyline over currently-empty cells. Its head is
// chosen at an endpoint whose straight forward path to the edge is currently
// clear. Because we only ever place a line whose head path is clear of
// already-placed lines, removing lines in reverse placement order is always a
// valid solution — and since removing a line only frees cells, no play order
// can ever dead-end.

import { DIRS, DIR_LIST, STARTING_LIVES } from './constants.js'
import { EMPTY, idx, inBounds } from './engine.js'

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

const OPP = { U: 'D', D: 'U', L: 'R', R: 'L' }
const PERP = { U: ['L', 'R'], D: ['L', 'R'], L: ['U', 'D'], R: ['U', 'D'] }

// Is the straight path beyond (r,c) in `dir` clear of occupied cells — and of
// the line's own cells (a bent line must not point back into its own body)?
function forwardClear(grid, rows, cols, r, c, dir, ownCells) {
  const [dr, dc] = DIRS[dir]
  let nr = r + dr
  let nc = c + dc
  while (inBounds(nr, nc, rows, cols)) {
    const i = idx(nr, nc, cols)
    if (grid[i] !== EMPTY || (ownCells && ownCells.has(i))) return false
    nr += dr
    nc += dc
  }
  return true
}

// Grow a self-avoiding polyline of bent segments over empty cells.
// Returns { cells, verts, segDirs } (tail → end) or null.
function growPolyline(grid, rows, cols, rng, maxSeg, maxLen) {
  let start = null
  for (let t = 0; t < 60; t++) {
    const r = Math.floor(rng() * rows)
    const c = Math.floor(rng() * cols)
    if (grid[idx(r, c, cols)] === EMPTY) {
      start = [r, c]
      break
    }
  }
  if (!start) return null

  const cells = [start]
  const verts = [start]
  const segDirs = []
  const used = new Set([idx(start[0], start[1], cols)])
  let cur = start
  let prevDir = null
  const segCount = 1 + Math.floor(rng() * maxSeg) // 1..maxSeg segments

  for (let s = 0; s < segCount; s++) {
    const choices = shuffle(prevDir ? PERP[prevDir].slice() : DIR_LIST.slice(), rng)
    let moved = false
    for (const dir of choices) {
      const [dr, dc] = DIRS[dir]
      const want = 2 + Math.floor(rng() * (maxLen - 1)) // 2..maxLen
      let steps = 0
      let cr = cur[0]
      let cc = cur[1]
      const seg = []
      while (steps < want) {
        const nr = cr + dr
        const nc = cc + dc
        if (!inBounds(nr, nc, rows, cols)) break
        const i = idx(nr, nc, cols)
        if (grid[i] !== EMPTY || used.has(i)) break
        cr = nr
        cc = nc
        used.add(i)
        seg.push([nr, nc])
        steps++
      }
      if (steps >= 1) {
        for (const cell of seg) cells.push(cell)
        cur = [cr, cc]
        verts.push(cur)
        segDirs.push(dir)
        prevDir = dir
        moved = true
        break
      }
    }
    if (!moved) break
  }

  if (verts.length < 2) return null
  return { cells, verts, segDirs }
}

/**
 * Build a solvable board of bent lines.
 * @returns {{ grid, arrows, rows, cols, count }}
 */
export function generateLevel(rows, cols, opts = {}) {
  const { fill = 0.55, maxSeg = 4, maxLen = 5, seed } = opts
  const rng = opts.rng || (seed != null ? mulberry32(seed) : Math.random)

  const grid = new Array(rows * cols).fill(EMPTY)
  const arrows = {}
  const target = Math.max(1, Math.floor(rows * cols * fill))

  let id = 0
  let occupied = 0
  let attempts = 0
  const maxAttempts = rows * cols * 12

  while (occupied < target && attempts < maxAttempts) {
    attempts++
    const poly = growPolyline(grid, rows, cols, rng, maxSeg, maxLen)
    if (!poly) continue

    const { cells, verts, segDirs } = poly
    const n = verts.length
    const ownCells = new Set(cells.map(([r, c]) => idx(r, c, cols)))

    // Candidate heads: either endpoint, pointing outward along its end segment.
    const endHead = verts[n - 1]
    const endDir = segDirs[n - 2]
    const startHead = verts[0]
    const startDir = OPP[segDirs[0]]

    const candidates = shuffle(
      [
        { head: endHead, dir: endDir, reverse: false },
        { head: startHead, dir: startDir, reverse: true },
      ],
      rng,
    )

    let chosen = null
    for (const cand of candidates) {
      if (
        forwardClear(grid, rows, cols, cand.head[0], cand.head[1], cand.dir, ownCells)
      ) {
        chosen = cand
        break
      }
    }
    if (!chosen) continue

    const orderedCells = chosen.reverse ? cells.slice().reverse() : cells
    const orderedVerts = chosen.reverse ? verts.slice().reverse() : verts

    for (const [r, c] of orderedCells) grid[idx(r, c, cols)] = id
    arrows[id] = {
      id,
      dir: chosen.dir,
      head: chosen.head,
      cells: orderedCells,
      verts: orderedVerts,
    }
    id++
    occupied += orderedCells.length
  }

  return { grid, arrows, rows, cols, count: Object.keys(arrows).length }
}

/** Difficulty knobs that scale with the level number. */
export function levelConfig(level) {
  const size = Math.min(8 + Math.floor((level - 1) / 2), 16)
  const fill = Math.min(0.45 + (level - 1) * 0.02, 0.68)
  const maxSeg = Math.min(3 + Math.floor((level - 1) / 3), 5)
  return { rows: size, cols: size, fill, maxSeg, maxLen: 5, lives: STARTING_LIVES }
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
    maxSeg: cfg.maxSeg,
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
  }
}
