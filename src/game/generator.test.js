import { test } from 'node:test'
import assert from 'node:assert/strict'
import { generateLevel, createGame, levelConfig } from './generator.js'
import { isSolvable, idx, EMPTY } from './engine.js'

test('generated boards are always solvable across many seeds and sizes', () => {
  for (let seed = 1; seed <= 200; seed++) {
    const size = 6 + (seed % 9) // 6..14
    const { grid, arrows, rows, cols, count } = generateLevel(size, size, {
      fill: 0.6,
      seed,
    })
    assert.ok(count > 0, `seed ${seed}: expected some lines`)
    assert.ok(
      isSolvable(grid, arrows, rows, cols),
      `seed ${seed} (${size}x${size}) produced an unsolvable board`,
    )
  }
})

test('lines never overlap and the grid matches the arrow set', () => {
  const { grid, arrows, rows, cols } = generateLevel(14, 14, { fill: 0.6, seed: 9 })
  const seen = new Array(rows * cols).fill(EMPTY)
  for (const id of Object.keys(arrows)) {
    for (const [r, c] of arrows[id].cells) {
      const i = idx(r, c, cols)
      assert.equal(seen[i], EMPTY, `cell ${r},${c} used by two lines`)
      seen[i] = Number(id)
      assert.equal(grid[i], Number(id), `grid mismatch at ${r},${c}`)
    }
  }
})

test('lines are bent and lengthy (multi-segment)', () => {
  const { arrows } = generateLevel(14, 14, { fill: 0.6, seed: 4 })
  const list = Object.values(arrows)
  const lens = list.map((a) => a.cells.length)
  const bentCount = list.filter((a) => a.verts.length >= 3).length
  assert.ok(Math.max(...lens) >= 4, 'expected some long lines')
  assert.ok(bentCount > 0, 'expected at least one bent (multi-segment) line')
  // head must be an endpoint of the cell chain
  for (const a of list) {
    const last = a.cells[a.cells.length - 1]
    assert.deepEqual(a.head, last, 'head should be the last cell (tail→head order)')
  }
})

test('createGame yields a playable, solvable state for many levels', () => {
  for (let level = 1; level <= 20; level++) {
    const g = createGame(level)
    assert.equal(g.status, 'playing')
    assert.equal(g.lives, 3)
    assert.equal(g.count, Object.keys(g.arrows).length)
    assert.ok(g.count > 0)
    assert.ok(isSolvable(g.grid, g.arrows, g.rows, g.cols), `level ${level} unsolvable`)
  }
})

test('difficulty scales with level', () => {
  const a = levelConfig(1)
  const b = levelConfig(12)
  assert.ok(b.rows >= a.rows)
  assert.ok(b.fill >= a.fill)
})
