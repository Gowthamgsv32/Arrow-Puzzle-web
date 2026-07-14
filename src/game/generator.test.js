import { test } from 'node:test'
import assert from 'node:assert/strict'
import { generateLevel, createGame, levelConfig } from './generator.js'
import { isSolvable, idx, EMPTY } from './engine.js'
import { shapeMask } from './shapes.js'

test('generated boards are always solvable across many seeds and shapes', () => {
  const shapes = ['heart', 'ball', 'star', 'apple', 'diamond']
  for (let seed = 1; seed <= 150; seed++) {
    const size = 16 + (seed % 9) // 16..24
    const mask = shapeMask(shapes[seed % shapes.length], size)
    const { grid, arrows, rows, cols, count } = generateLevel(size, size, {
      mask,
      seed,
    })
    assert.ok(count > 0, `seed ${seed}: expected some lines`)
    assert.ok(
      isSolvable(grid, arrows, rows, cols),
      `seed ${seed} (${size}) produced an unsolvable board`,
    )
  }
})

test('the shape is filled completely — no interior gaps', () => {
  for (let seed = 1; seed <= 40; seed++) {
    const size = 18 + (seed % 6)
    const mask = shapeMask('heart', size)
    const { grid, arrows, cols } = generateLevel(size, size, { mask, seed })
    // Every masked cell belongs to exactly one line...
    let covered = 0
    for (const i of mask) {
      assert.notEqual(grid[i], EMPTY, `seed ${seed}: gap at cell ${i}`)
      covered++
    }
    // ...and no line strays outside the mask.
    for (const id of Object.keys(arrows)) {
      for (const [r, c] of arrows[id].cells) {
        assert.ok(mask.has(idx(r, c, cols)), `seed ${seed}: line ${id} left the shape`)
      }
    }
    assert.equal(covered, mask.size)
  }
})

test('lines never overlap and the grid matches the arrow set', () => {
  const mask = shapeMask('ball', 20)
  const { grid, arrows, cols } = generateLevel(20, 20, { mask, seed: 9 })
  const seen = new Set()
  for (const id of Object.keys(arrows)) {
    for (const [r, c] of arrows[id].cells) {
      const i = idx(r, c, cols)
      assert.ok(!seen.has(i), `cell ${r},${c} used by two lines`)
      seen.add(i)
      assert.equal(grid[i], Number(id))
    }
  }
})

test('lines are bent and there are many of them', () => {
  const mask = shapeMask('heart', 22)
  const { arrows } = generateLevel(22, 22, { mask, seed: 4 })
  const list = Object.values(arrows)
  assert.ok(list.length >= 20, `expected many lines, got ${list.length}`)
  assert.ok(list.some((a) => a.verts.length >= 3), 'expected some bent lines')
  for (const a of list) {
    assert.deepEqual(a.head, a.cells[a.cells.length - 1], 'head should be the last cell')
  }
})

test('createGame yields a playable, fully-solvable state for many levels', () => {
  for (let level = 1; level <= 20; level++) {
    const g = createGame(level)
    assert.equal(g.status, 'playing')
    assert.equal(g.count, Object.keys(g.arrows).length)
    assert.ok(g.count > 0)
    assert.ok(isSolvable(g.grid, g.arrows, g.rows, g.cols), `level ${level} unsolvable`)
  }
})

test('difficulty scales with level', () => {
  const a = levelConfig(1)
  const b = levelConfig(16)
  assert.ok(b.rows >= a.rows)
  assert.ok(b.maxLen >= a.maxLen)
})
