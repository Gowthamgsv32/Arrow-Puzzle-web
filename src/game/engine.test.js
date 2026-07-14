import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  EMPTY,
  idx,
  occupiedCells,
  boundingBox,
  headForwardCells,
  isReleasable,
  tryRelease,
  isSolvable,
} from './engine.js'

// Build a grid from a list of arrows on a rows x cols board.
function build(rows, cols, arrowList) {
  const grid = new Array(rows * cols).fill(EMPTY)
  const arrows = {}
  for (const a of arrowList) {
    arrows[a.id] = a
    for (const [r, c] of occupiedCells(a)) grid[idx(r, c, cols)] = a.id
  }
  return {
    rows,
    cols,
    grid,
    arrows,
    count: arrowList.length,
    lives: 3,
    status: 'playing',
    level: 1,
  }
}

test('occupiedCells lays the body out behind the head', () => {
  // Head at (2,3) pointing Right, length 3 -> cells (2,3),(2,2),(2,1)
  assert.deepEqual(occupiedCells({ id: 0, dir: 'R', len: 3, r: 2, c: 3 }), [
    [2, 3],
    [2, 2],
    [2, 1],
  ])
  // Head at (0,1) pointing Down, length 2 -> (0,1),(-1,1) back is up
  assert.deepEqual(occupiedCells({ id: 0, dir: 'D', len: 2, r: 1, c: 1 }), [
    [1, 1],
    [0, 1],
  ])
})

test('boundingBox spans the whole piece', () => {
  const box = boundingBox({ id: 0, dir: 'R', len: 3, r: 2, c: 3 })
  assert.deepEqual(box, { minR: 2, minC: 1, spanR: 1, spanC: 3 })
})

test('headForwardCells walks from the head to the edge', () => {
  // Head (1,1) Right on 3x3 -> (1,2)
  assert.deepEqual(headForwardCells({ dir: 'R', r: 1, c: 1 }, 3, 3), [[1, 2]])
})

test('isReleasable checks only the cells ahead of the head', () => {
  // 5-wide row. Arrow A: head (0,2) Right, len 2 -> occupies (0,2),(0,1).
  // Arrow B: head (0,4) Right, len 1 -> occupies (0,4). Ahead of A's head is
  // (0,3),(0,4); (0,4) is taken -> A blocked. B has clear edge -> releasable.
  const A = { id: 0, dir: 'R', len: 2, r: 0, c: 2 }
  const B = { id: 1, dir: 'R', len: 1, r: 0, c: 4 }
  const s = build(1, 5, [A, B])
  assert.equal(isReleasable(s.grid, A, 1, 5), false)
  assert.equal(isReleasable(s.grid, B, 1, 5), true)
})

test('releasing an arrow clears all its cells and can win', () => {
  const A = { id: 0, dir: 'R', len: 3, r: 0, c: 2 } // (0,2)(0,1)(0,0)
  const s = build(1, 4, [A]) // ahead of head is (0,3) empty -> releasable
  const { state, result, arrow } = tryRelease(s, 0)
  assert.equal(result, 'released')
  assert.equal(arrow.id, 0)
  for (const [r, c] of occupiedCells(A)) assert.equal(state.grid[idx(r, c, 4)], EMPTY)
  assert.equal(state.count, 0)
  assert.equal(state.status, 'won')
})

test('a blocked release costs a life and removes nothing', () => {
  const A = { id: 0, dir: 'R', len: 1, r: 0, c: 0 }
  const B = { id: 1, dir: 'L', len: 1, r: 0, c: 2 }
  const s = build(1, 3, [A, B]) // A ahead: (0,1),(0,2); (0,2) taken -> blocked
  s.lives = 2
  const { state, result } = tryRelease(s, 0)
  assert.equal(result, 'blocked')
  assert.equal(state.lives, 1)
  assert.equal(state.count, 2)
  assert.equal(state.status, 'playing')
})

test('losing the final life ends the game', () => {
  const A = { id: 0, dir: 'R', len: 1, r: 0, c: 0 }
  const B = { id: 1, dir: 'L', len: 1, r: 0, c: 2 }
  const s = build(1, 3, [A, B])
  s.lives = 1
  const { state, result } = tryRelease(s, 0)
  assert.equal(result, 'blocked')
  assert.equal(state.lives, 0)
  assert.equal(state.status, 'lost')
})

test('no interaction once the game is over', () => {
  const A = { id: 0, dir: 'R', len: 1, r: 0, c: 0 }
  const s = build(1, 1, [A])
  s.status = 'won'
  assert.equal(tryRelease(s, 0).result, 'none')
})

test('isSolvable distinguishes jammed from clearable boards', () => {
  // R _ L pointing at each other across an empty middle -> deadlock.
  const jammed = build(1, 3, [
    { id: 0, dir: 'R', len: 1, r: 0, c: 0 },
    { id: 1, dir: 'L', len: 1, r: 0, c: 2 },
  ])
  assert.equal(isSolvable(jammed.grid, jammed.arrows, 1, 3), false)

  // L _ R pointing outward -> solvable.
  const easy = build(1, 3, [
    { id: 0, dir: 'L', len: 1, r: 0, c: 0 },
    { id: 1, dir: 'R', len: 1, r: 0, c: 2 },
  ])
  assert.equal(isSolvable(easy.grid, easy.arrows, 1, 3), true)
})
