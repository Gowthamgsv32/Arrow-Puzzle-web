import { test } from 'node:test'
import assert from 'node:assert/strict'
import { generateBoard, createGame, levelConfig } from './generator.js'
import { isSolvable, countArrows } from './engine.js'

test('generated boards are always solvable across many seeds and sizes', () => {
  for (let seed = 1; seed <= 200; seed++) {
    const size = 4 + (seed % 9) // 4..12
    const { board, rows, cols, arrows } = generateBoard(size, size, {
      fill: 0.9,
      seed,
    })
    assert.ok(arrows > 0, `seed ${seed}: expected some arrows`)
    assert.ok(
      isSolvable(board, rows, cols),
      `seed ${seed} (${size}x${size}) produced an unsolvable board`,
    )
  }
})

test('fill ratio is respected and arrow count matches the board', () => {
  const { board, arrows } = generateBoard(10, 10, { fill: 0.8, seed: 42 })
  assert.equal(arrows, countArrows(board))
  assert.ok(arrows >= 60, `expected a dense board, got ${arrows} arrows`)
})

test('createGame yields a playable, solvable state', () => {
  for (let level = 1; level <= 20; level++) {
    const g = createGame(level)
    assert.equal(g.status, 'playing')
    assert.equal(g.lives, 3)
    assert.equal(g.arrows, countArrows(g.board))
    assert.ok(isSolvable(g.board, g.rows, g.cols), `level ${level} unsolvable`)
  }
})

test('difficulty scales monotonically with level', () => {
  const a = levelConfig(1)
  const b = levelConfig(10)
  assert.ok(b.rows >= a.rows)
  assert.ok(b.fill >= a.fill)
})
