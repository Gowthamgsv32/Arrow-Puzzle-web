import { test } from 'node:test'
import assert from 'node:assert/strict'
import { generateLevel, createGame, levelConfig } from './generator.js'
import { isSolvable, occupiedCells, idx, EMPTY } from './engine.js'

// Total cells occupied by all arrows.
function occupiedCount(arrows) {
  let n = 0
  for (const id of Object.keys(arrows)) n += arrows[id].len
  return n
}

test('generated boards are always solvable across many seeds and sizes', () => {
  for (let seed = 1; seed <= 200; seed++) {
    const size = 4 + (seed % 9) // 4..12
    const { grid, arrows, rows, cols, count } = generateLevel(size, size, {
      fill: 0.9,
      maxLen: 5,
      seed,
    })
    assert.ok(count > 0, `seed ${seed}: expected some arrows`)
    assert.ok(
      isSolvable(grid, arrows, rows, cols),
      `seed ${seed} (${size}x${size}) produced an unsolvable board`,
    )
  }
})

test('arrows never overlap and the grid matches the arrow set', () => {
  const { grid, arrows, rows, cols } = generateLevel(10, 10, {
    fill: 0.85,
    maxLen: 5,
    seed: 7,
  })
  // Every arrow cell points back to that arrow id; no double-booking.
  const seen = new Array(rows * cols).fill(EMPTY)
  for (const id of Object.keys(arrows)) {
    for (const [r, c] of occupiedCells(arrows[id])) {
      const i = idx(r, c, cols)
      assert.equal(seen[i], EMPTY, `cell ${r},${c} used twice`)
      seen[i] = Number(id)
      assert.equal(grid[i], Number(id), `grid mismatch at ${r},${c}`)
    }
  }
})

test('arrows have real length (the "lengthy" look)', () => {
  const { arrows } = generateLevel(10, 10, { fill: 0.85, maxLen: 5, seed: 3 })
  const lens = Object.values(arrows).map((a) => a.len)
  const avg = lens.reduce((s, n) => s + n, 0) / lens.length
  assert.ok(Math.max(...lens) >= 3, 'expected some long arrows')
  assert.ok(avg > 1.4, `expected a lengthy average, got ${avg.toFixed(2)}`)
})

test('createGame yields a playable, solvable state for many levels', () => {
  for (let level = 1; level <= 20; level++) {
    const g = createGame(level)
    assert.equal(g.status, 'playing')
    assert.equal(g.lives, 3)
    assert.equal(g.count, Object.keys(g.arrows).length)
    assert.ok(occupiedCount(g.arrows) > 0)
    assert.ok(isSolvable(g.grid, g.arrows, g.rows, g.cols), `level ${level} unsolvable`)
  }
})

test('difficulty scales with level', () => {
  const a = levelConfig(1)
  const b = levelConfig(12)
  assert.ok(b.rows >= a.rows)
  assert.ok(b.fill >= a.fill)
  assert.ok(b.maxLen >= a.maxLen)
})
